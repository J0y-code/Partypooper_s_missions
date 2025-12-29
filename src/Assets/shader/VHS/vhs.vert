#version 130

// --- MÉTADONNÉES DE LICENCE ---
// LICENCE : Ce fichier est considéré comme Open Source/Permissif.
// (La licence propriétaire générale du projet ne s'applique pas à ce fichier, 
// conformément à la section 'Exception générale' du fichier LICENSE.)
// AUTEUR : PFLIEGER-CHAKMA Nathan alias J0ytheC0de

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 texcoord;

uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
}
