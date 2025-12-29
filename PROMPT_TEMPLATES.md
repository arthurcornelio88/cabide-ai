# Fashion Pipeline Templates

## System Instruction
You are an elite fashion photographer and senior AI prompt engineer. Your goal is to generate photorealistic imagery with 100% garment fidelity. You must strictly preserve the color, texture, and silhouette of the provided reference images.

## Template: Virtual Model Quotidien
Generate a high-fidelity 8k lifestyle photograph of a professional, non-recognizable female model.

**Garment Type**: {{garment_type}}

Instructions based on garment type:
- If it's a "sapato" (shoe): Create a full outfit with the model wearing these EXACT shoes. Add complementary clothing (dress, pants, or skirt) that matches the shoes' style. Focus the composition to prominently feature the shoes while showing the complete look.
- If it's clothing (vestido, calça, saia, veste, etc.): The model is wearing the exact garment shown in the reference images (Image 1 is Front view, Image 2 is Back view if provided). Complete the outfit with appropriate complementary items if needed.
- If it's an accessory (écharpe, bracelete): The model is wearing the exact accessory shown. Create a complete, stylish outfit that highlights the accessory.

The setting is a {{environment}}, capturing an authentic "quotidien" moment like {{activity}}.
Ensure the lighting matches the environment (e.g., dappled sunlight for forests, golden hour for beaches).
Focus on realistic fabric draping, natural folds, and a shallow depth of field (f/1.8).
Photography style: Cinematic, shot on a 35mm prime lens, high dynamic range.

CRITICAL: The {{garment_type}} shown in the reference image(s) must be EXACTLY reproduced with 100% color, texture, and design fidelity.

## Template: Virtual Model Party
Generate an ultra-high-end 8k editorial photograph of a professional fashion model.

**Garment Type**: {{garment_type}}

The model is wearing the luxury "vestido de festa" shown in the reference images.
The setting is a high-society party in {{environment}}, with elegant decor, soft bokeh lighting from chandeliers, and a sophisticated atmosphere.
The model is {{activity}}.
Technical: Preserve the shimmer of the fabric and the intricate details of the dress.
Photography style: Vogue-style editorial, dramatic lighting, 50mm lens.

CRITICAL: The {{garment_type}} shown in the reference image(s) must be EXACTLY reproduced with 100% color, texture, and design fidelity.
