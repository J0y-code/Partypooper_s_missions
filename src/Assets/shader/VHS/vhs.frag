#version 130

// --- MÉTADONNÉES DE LICENCE ---
// LICENCE : Ce fichier est considéré comme Open Source/Permissif.
// (La licence propriétaire générale du projet ne s'applique pas à ce fichier, 
// conformément à la section 'Exception générale' du fichier LICENSE.)
// AUTEUR : PFLIEGER-CHAKMA Nathan alias J0ytheC0de

uniform sampler2D sceneTex;
uniform float time;
uniform float vhs_strength;
uniform float curvature;

in vec2 texcoord;
out vec4 fragColor;

float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898,78.233))) * 43758.5453);
}

// CRT mask (triad pattern)
vec3 crt_mask(vec2 uv) {
    float mask = fract(uv.x * 800.0);
    return vec3(
        smoothstep(0.0, 0.33, mask),
        smoothstep(0.33, 0.66, mask),
        smoothstep(0.66, 1.0, mask)
    );
}

void main() 
{
    // -------------------------
    // 1. CRT curvature
    // -------------------------
    vec2 uv = texcoord - 0.5;
    uv *= 1.0 + curvature * dot(uv, uv);
    uv += 0.5;
    uv = clamp(uv, 0.000001, 0.99999);

    // -------------------------
    // 2. VHS horizontal wobble
    // -------------------------
    float wobble = sin(uv.y * 300.0 + time * 8.0) * 0.001;
    uv.x += wobble;

    // Rolling vertical offset
    uv.y += sin(time * 0.35) * 0.003;

    // -------------------------
    // 3. Chromatic aberration
    // -------------------------
    float ca = 0.0015 + sin(time * 4.0) * 0.001;

    vec2 uv_r = clamp(uv + vec2(ca, 0.0), 0.0, 1.0);
    vec2 uv_b = clamp(uv - vec2(ca, 0.0), 0.0, 1.0);

    vec3 col;
    col.r = texture(sceneTex, uv_r).r;
    col.g = texture(sceneTex, uv).g;
    col.b = texture(sceneTex, uv_b).b;

    // -------------------------
    // 4. Ghosting (CRT persistence)
    // -------------------------
    vec2 ghost_uv = uv + vec2(-0.01, 0.0);
    vec3 ghost = texture(sceneTex, ghost_uv).rgb * 0.025;
    col += ghost;

    // -------------------------
    // 5. Tape noise (horizontal bands)
    // -------------------------
    float noise_line = rand(vec2(time * 50.0, uv.y * 1000.0)) * 0.02;
    col += noise_line;

    // Interference lines moving downward
    float line = sin(uv.y * 600.0 + time * 30.0) * 0.003;
    col *= 1.0 + line;

    // -------------------------
    // 6. Saturation flicker
    // -------------------------
    float sat = 1.0 + sin(time * 3.2) * 0.006;
    float luma = dot(col, vec3(0.299, 0.587, 0.114));
    col = mix(vec3(luma), col, sat);

    // -------------------------
    // 7. Scanlines améliorés
    // -------------------------
    float scan = 0.85 + 0.15 * sin(uv.y * 1200.0);
    col *= scan;

    // CRT RGB mask
    col *= mix(vec3(1.0), crt_mask(uv * 1.0), 0.25);

    // -------------------------
    // 8. Cheap bloom
    // -------------------------
    vec3 bright = max(vec3(0), col - 0.8);
    col += bright * 0.1;

    // -------------------------
    // 9. Mix final
    // -------------------------
    vec3 original = texture(sceneTex, texcoord).rgb;
    vec3 final_col = mix(original, col, vhs_strength);

    fragColor = vec4(final_col, vhs_strength);
}