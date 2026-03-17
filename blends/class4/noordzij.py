from coldtype import *
from coldtype.blender import *

"""
A classic 5-by-5 Noordzij Cube, displaying any
variable font with three axes

(https://letterror.com/articles/noordzij-cube.html)
"""

fnt, fs = Font.Find("ObviouslyV"), 0.75
axes = lambda x, y, z: {"slnt": x, "wdth":y, "wght":z}

if 0:
    fnt, fs = Font.Find("AT-NameSansVariable.Edu.ttf"), 1
    axes = lambda x, y, z: {"ital": x, "wght":y, "opsz":z}

d = 5

@b3d_runnable()
def setup(bpw:BpyWorld):
    (bpw.delete_previous()
        .cycles(128, False, Rect(1920, 1920))
        .timeline(Timeline(240)
            , resetFrame=0
            , output=setup.output_folder / "noord1_"))
    
    (BpyObj.Cube("Floor")
        .dimensions(x=d*2, y=d*2, z=0.25)
        .locate(z=-0.5)
        .hide()
        .material("floor_mat", lambda m: m
            .f(0)
            .specular(0)
            .roughness(1)))
    
    pivot = (BpyObj.Empty("Center")
        .insert_keyframes("rotation_euler",
            (0, lambda bp: bp.rotate()),
            (240, lambda bp: bp.rotate(z=-360)))
        .make_keyframes_linear("rotation_euler"))
    
    BpyObj.Find("Camera").parent(pivot)
    
    def add_glyph(x, y, z):
        (BpyObj.Curve(f"Glyph_{x}_{y}_{z}")
            .draw(StSt("A", fnt, fs, **axes(x, y, z))
                .centerZero()
                .pen())
            .rotate(x=90)
            .locate(x=(x*d)-d*0.5, y=(y*d)-d*0.5, z=z*d)
            .extrude(0.01)
            .convert_to_mesh()
            .material(f"letter_mat_{y}", lambda m: m
                .f(1)
                .f(hsl(0.2+y*0.5, 1, 0.65))
                .specular(0)
                .roughness(1)))
    
    for z in range(0, d):
        for y in range(0, d):
            for x in range(0, d):
                add_glyph(x/(d-1), y/(d-1), z/(d-1))

    
    alt_camera = bpy.data.cameras["Camera.001"]
    alt_camera.dof.focus_object = BpyObj.Find("Glyph_0.75_0.0_0.75").obj