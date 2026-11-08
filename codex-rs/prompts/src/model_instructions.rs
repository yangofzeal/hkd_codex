//! Adds local task-continuity instructions to captured model instructions.
//! Missing templates produce a warning; supplied empty templates remain valid input.

use crate::ResolvedModelMessages;
use codex_protocol::openai_models::ModelInfo;

/// Renders base instructions from the caller's captured model, retaining missing-template warnings.
pub fn render_model_instructions(model_info: &ModelInfo) -> String {
    let template = ResolvedModelMessages::from_model(model_info).instructions_template();
    if template.is_none() {
        tracing::warn!(
            model = %model_info.slug,
            "Model has no instruction template; returning empty instructions."
        );
    }
    crate::task_continuity::append_task_continuity(template.unwrap_or_default())
}

#[cfg(test)]
#[path = "model_instructions_tests.rs"]
mod tests;
