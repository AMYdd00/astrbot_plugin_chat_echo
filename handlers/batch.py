import asyncio
import time

from astrbot.api.message_components import Plain
from astrbot.core.message.message_event_result import MessageEventResult

from ..helpers import extract_bot_text
from .proactive import handle_proactive_batch
from .reply import handle_reply_batch


async def schedule_batch_flush_reply(plugin, tracker, event, group_id, umo, delay):
    """Wait for dynamic silence period, then flush reply batch.
    Since this runs asynchronously AFTER the pipeline has ended,
    we must generate and send the reply directly rather than setting event flags."""
    try:
        await asyncio.sleep(delay)
        if not tracker.alive:
            return
        if tracker.analyzing or plugin.tracker_manager.is_active_thinking(group_id):
            return
        if not tracker.batch_buffer:
            return

        plugin.logger.info(
            f"[Batch] Flushing reply batch ({len(tracker.batch_buffer)} msgs) in group {group_id}"
        )
        await flush_batch_reply_scheduled(plugin, tracker, event, group_id, umo)
    except asyncio.CancelledError:
        pass
    except Exception:
        plugin.logger.exception("[Batch] Error in scheduled reply flush")


async def flush_batch_reply_scheduled(plugin, tracker, event, group_id, umo):
    """Scheduled batch flush: analyzer -> direct LLM generation -> send.
    Called from async task after pipeline has already completed."""
    if tracker.analyzing or plugin.tracker_manager.is_active_thinking(group_id):
        return

    batch = plugin.tracker_manager.clear_batch_state(tracker)
    if not batch:
        return

    tracker.analyzing = True
    plugin.tracker_manager.set_active_thinking(group_id, True)
    try:
        # Step 1: analyze whether to reply
        res = await handle_reply_batch(plugin, tracker, event, batch)
        if not res:
            return

        # Step 2: get persona and provider
        persona_name = ""
        personality = None
        try:
            personality = await plugin.context.persona_manager.get_default_persona_v3(umo)
            if personality:
                persona_name = personality.get("name") or ""
        except Exception:
            pass

        provider_id = plugin.config_helper.generator_provider()
        if not provider_id and umo:
            try:
                provider_id = await plugin.context.get_current_chat_provider_id(umo)
            except Exception:
                pass
        if not provider_id:
            plugin.logger.warning(f"[BatchScheduled] No provider available for group {group_id}")
            return

        # Step 3: build system_prompt from persona
        system_prompt = ""
        custom_prompt = plugin.config_helper.get_custom_persona_prompt(persona_name)
        if custom_prompt:
            system_prompt = custom_prompt.strip()
        elif personality and personality.get("prompt"):
            system_prompt = personality["prompt"].strip()
        if not system_prompt:
            plugin.logger.warning(f"[BatchScheduled] No persona prompt for group {group_id}")
            return

        self_id = event.get_self_id()
        identity_hint = f"你的账号ID/QQ号是: {self_id}" if self_id else ""
        if identity_hint:
            system_prompt = identity_hint + "\n" + system_prompt

        # Append short_hint (same as on_llm_request)
        short_hint = "\n\n[系统提示：你刚才收到了一些仅供理解上下文的辅助信息（如图片描述）。忽略那些信息的分析格式，你仍然是你，按你的性格随口接一句话——和平时一样短，禁止分析式回复。]"
        system_prompt += short_hint

        # Step 4: build user prompt from conversation context
        context_lines = []
        if tracker.trigger_message:
            context_lines.append(f"{tracker.trigger_user_name}: {tracker.trigger_message}")
        if tracker.bot_message:
            context_lines.append(f"你: {tracker.bot_message}")
        for msg in tracker.collected[-10:]:
            if msg.get("user_id") == "bot":
                continue
            context_lines.append(f"{msg['user_name']}: {msg['content']}")
        for msg in batch:
            context_lines.append(f"{msg['user_name']}: {msg['content']}")

        user_prompt = "以下是最近的群聊对话，请以你的角色身份随口接一句话：\n\n" + "\n".join(context_lines)

        # Step 5: call LLM
        plugin.logger.info(f"[BatchScheduled] Generating reply for group {group_id}...")
        try:
            resp = await asyncio.wait_for(
                plugin.context.llm_generate(
                    prompt=user_prompt,
                    chat_provider_id=provider_id,
                    system_prompt=system_prompt,
                ),
                timeout=60,
            )
        except asyncio.TimeoutError:
            plugin.logger.warning(f"[BatchScheduled] LLM generation timed out for group {group_id}")
            return

        if resp is None:
            plugin.logger.warning(f"[BatchScheduled] LLM returned None for group {group_id}")
            return

        text = extract_bot_text(resp)
        if not text or not text.strip():
            return

        text = text.strip()

        # Step 6: send reply
        result = MessageEventResult()
        result.chain = [Plain(text)]
        try:
            await event.send(result)
            plugin.logger.info(f"[BatchScheduled] Sent reply to group {group_id}: {text[:80]}")
        except Exception as e:
            plugin.logger.exception(f"[BatchScheduled] Failed to send reply in group {group_id}: {e}")
            return

        # Step 7: update tracker with bot's reply for future context
        tracker.collected.append({
            "user_name": "你",
            "user_id": "bot",
            "content": text,
            "image_urls": [],
            "time": time.time(),
            "is_at_bot": False,
        })
        tracker.detection_count = 0
        tracker.expire_at = time.time() + plugin.config_helper.track_timeout()
    except Exception:
        plugin.logger.exception(f"[BatchScheduled] Error in scheduled batch flush: {e}")
    finally:
        tracker.analyzing = False
        plugin.tracker_manager.set_active_thinking(group_id, False)


async def flush_batch_reply(plugin, tracker, event, group_id, umo):
    """Flush accumulated batch messages for reply analysis and trigger if appropriate.
    Called synchronously from process_group_message when trigger_now is True (@bot or batch_full)."""
    if tracker.analyzing or plugin.tracker_manager.is_active_thinking(group_id):
        return

    batch = plugin.tracker_manager.clear_batch_state(tracker)
    if not batch:
        return

    tracker.analyzing = True
    try:
        res = await handle_reply_batch(plugin, tracker, event, batch)
        if res:
            event.is_at_or_wake_command = True
            event.set_extra("chat_echo_triggered", True)
            event.set_extra("chat_echo_mode", "reply")
            event.set_extra(
                "selected_provider", plugin.config_helper.generator_provider()
            )
            plugin.tracker_manager.set_active_thinking(group_id, True)
    finally:
        tracker.analyzing = False


async def schedule_batch_flush_proactive(plugin, group_id, delay):
    """Wait for dynamic silence period, then flush proactive batch."""
    try:
        await asyncio.sleep(delay)
        buf = plugin.tracker_manager.get_proactive_buffer(group_id)
        if not buf or not buf["buffer"]:
            return
        if plugin.tracker_manager.is_active_thinking(group_id):
            return

        event = buf.get("event")
        umo = buf.get("umo", "")
        plugin.logger.info(
            f"[ProactiveBatch] Flushing proactive batch ({len(buf['buffer'])} msgs) in group {group_id}"
        )
        if event:
            await flush_batch_proactive(plugin, event, group_id, umo)
    except asyncio.CancelledError:
        return
    except Exception:
        plugin.logger.exception("[ProactiveBatch] Error in scheduled proactive flush")
        return


async def flush_batch_proactive(plugin, event, group_id, umo):
    """Flush accumulated proactive batch for participation analysis."""
    if plugin.tracker_manager.is_active_thinking(group_id):
        return

    batch = plugin.tracker_manager.clear_proactive_buffer(group_id)
    if not batch:
        return

    plugin.tracker_manager.set_active_thinking(group_id, True)
    try:
        res = await handle_proactive_batch(plugin, event, batch)
        if res:
            event.is_at_or_wake_command = True
            event.set_extra("chat_echo_triggered", True)
            event.set_extra("chat_echo_mode", "proactive")
            event.set_extra(
                "selected_provider", plugin.config_helper.generator_provider()
            )
    finally:
        plugin.tracker_manager.set_active_thinking(group_id, False)
