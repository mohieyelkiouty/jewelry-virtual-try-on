"""Convert STL, OBJ or GLB meshes into lightweight GLB files with a gold PBR material.

Examples:
    python tools/mesh_to_glb.py source/bangle.stl models/bangles/bangle-002.glb
    python tools/mesh_to_glb.py source/set.glb --inspect
    python tools/mesh_to_glb.py source/set.glb models/bangles/bangle.glb --parts 0,2,3
"""
import argparse
import os
import sys

import trimesh
from trimesh.visual import TextureVisuals
from trimesh.visual.material import PBRMaterial

GOLD = PBRMaterial(baseColorFactor=[240, 192, 64, 255], metallicFactor=1.0, roughnessFactor=0.28)


def load_parts(path):
    scene = trimesh.load(path, force="scene")
    return [g for g in scene.dump() if isinstance(g, trimesh.Trimesh)]


def optimize(mesh, faces):
    mesh = mesh.copy()
    mesh.merge_vertices()
    if len(mesh.faces) > faces:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=faces)
        except TypeError:
            mesh = mesh.simplify_quadric_decimation(faces)
    mesh.apply_translation(-mesh.bounds.mean(axis=0))
    mesh.fix_normals()
    mesh.visual = TextureVisuals(material=GOLD)
    return mesh


def write(mesh, dst):
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    mesh.export(dst)
    print(f"{dst}: {len(mesh.faces)} faces, {os.path.getsize(dst) / 1e6:.1f} MB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", help="destination .glb")
    ap.add_argument("--faces", type=int, default=120000, help="target face count (default: 120000)")
    ap.add_argument("--inspect", action="store_true", help="list the parts of the input and exit")
    ap.add_argument("--parts", help="comma-separated part indices to export as separate files")
    args = ap.parse_args()

    parts = load_parts(args.input)
    if args.inspect:
        print(f"{len(parts)} part(s)")
        for i, p in enumerate(parts):
            print(f"[{i:02d}] faces={len(p.faces):>8}  extents={[round(float(x), 2) for x in p.extents]}")
        return
    if not args.output:
        ap.error("output is required unless --inspect is used")

    if args.parts:
        stem, ext = os.path.splitext(args.output)
        for i in (int(x) for x in args.parts.split(",")):
            write(optimize(parts[i], args.faces), f"{stem}-{i:02d}{ext or '.glb'}")
    else:
        merged = trimesh.util.concatenate(parts) if len(parts) > 1 else parts[0]
        write(optimize(merged, args.faces), args.output)


if __name__ == "__main__":
    sys.exit(main())
