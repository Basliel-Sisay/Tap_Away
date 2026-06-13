VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;

uniform mat4 u_Model;
uniform mat4 u_View;
uniform mat4 u_Projection;

out vec3 vNormal;
out vec3 vFragPos;

void main() {
    vFragPos = vec3(u_Model * vec4(aPos, 1.0));
    vNormal = mat3(transpose(inverse(u_Model))) * aNormal;
    gl_Position = u_Projection * u_View * vec4(vFragPos, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec3 vNormal;
in vec3 vFragPos;

uniform vec3 u_Color;
uniform vec3 u_LightDir;

out vec4 FragColor;

void main() {
    vec3 norm = normalize(vNormal);
    vec3 light = normalize(u_LightDir);
    float diff = max(dot(norm, light), 0.0);

    // Lifted lighting: darker ambient, brighter key, subtle cool rim for edge read
    vec3 ambient = 0.18 * u_Color;
    vec3 diffuse = diff * u_Color * 1.15;
    float rim = pow(1.0 - max(dot(norm, vec3(0.0, 0.0, 1.0)), 0.0), 2.5);
    vec3 rimLight = vec3(0.35, 0.55, 0.85) * rim * 0.35;

    FragColor = vec4(ambient + diffuse + rimLight, 1.0);
}
"""

PICKER_FRAGMENT_SHADER = """
#version 330 core
uniform vec3 u_PickerColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(u_PickerColor, 1.0);
}
"""


UI_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;

uniform vec2 u_Offset;
uniform vec2 u_Size;
uniform vec2 u_ScreenSize;

out vec2 vUV;

void main() {
    vec2 pos = u_Offset + aPos * u_Size;
    vec2 ndc = vec2(
        (pos.x / u_ScreenSize.x) * 2.0 - 1.0,
        1.0 - (pos.y / u_ScreenSize.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    vUV = aPos;
}
"""

UI_FRAGMENT_SHADER = """
#version 330 core
in vec2 vUV;

uniform vec3 u_Color;
uniform vec3 u_Color2;
uniform vec2 u_Size;
uniform float u_Alpha;
uniform float u_Radius;
uniform float u_UseGradient;

out vec4 FragColor;

float roundedBox(vec2 p, vec2 halfSize, float radius) {
    vec2 d = abs(p) - halfSize + radius;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - radius;
}

void main() {
    vec2 halfSize = u_Size * 0.5;
    vec2 p = (vUV - 0.5) * u_Size;

    if (u_Radius > 0.0) {
        float dist = roundedBox(p, halfSize, u_Radius);
        if (dist > 1.0) discard;
        float edge = 1.0 - smoothstep(0.0, 1.0, dist);
        vec3 col = mix(u_Color, u_Color2, vUV.y * u_UseGradient);
        FragColor = vec4(col, u_Alpha * edge);
    } else {
        vec3 col = mix(u_Color, u_Color2, vUV.y * u_UseGradient);
        FragColor = vec4(col, u_Alpha);
    }
}
"""
