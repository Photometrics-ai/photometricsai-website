# Take-Action Context Generation Prompt

This prompt generates the `PRODUCT_CONTEXT` block used in `lambda_function.py`. Run it with the `photometrics-ai-messaging` skill loaded to produce an updated context block whenever the messaging strategy evolves.

## The Prompt

> We have a page at photometrics.ai/take-action which enables members of the public to choose from these priorities: Crime & Safety, Transportation Safety, Migratory Birds, Light Pollution, Energy Waste, Environmental Impact (plus a custom priority option).
>
> The page uses a two-stage AI pipeline: (1) Haiku with web search identifies local politicians who may be open to these ideas, (2) Sonnet writes a custom letter to those officials based on the citizen's selected priorities.
>
> Using the messaging skill, write the context block that Sonnet receives when generating these letters. This context must:
> - Frame the problem using the false choice concept (safety vs. darkness is a false binary; precision is the answer)
> - Provide narrative ammunition for each of the 6 priorities so Sonnet can write a compelling, specific paragraph per selection
> - Include sourced stats and verified product facts -- no fabricated numbers
> - Position the product as the bridge (how the gap gets closed), not the hero
> - Be written for the audience: a citizen persuading a local official to act
> - Target approximately 1,500-2,000 tokens to balance richness with API cost
> - End with the ask: a pilot program (include specifics)

## How to Use

1. Load the `photometrics-ai-messaging` skill
2. Run the prompt above
3. Review the output for accuracy against the messaging skill and financials skill
4. Replace the `PRODUCT_CONTEXT` string in `lambda_function.py`
5. Deploy: zip and `aws lambda update-function-code`

## Last Generated

2026-03-03 — Initial generation aligned with messaging skill enrichment (added narrative facts, Crime & Safety, Transportation Safety frameworks).
