bl_info = {
    "name": "TK BBox Batch Rename",
    "author": "tomanov",
    "version": (1, 2, 0),
    "blender": (4, 0, 0),
    "location": "F3 Search",
    "description": "Batch rename selected objects by bounding-box proximity",
    "category": "Object",
}

import bpy
from mathutils import Vector
from bpy.props import StringProperty


def bbox_center_world(obj):
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return sum(bbox, Vector()) / 8.0


class TK_OT_bbox_batch_rename(bpy.types.Operator):
    bl_idname = "tk.bbox_batch_rename"
    bl_label = "BBox Batch Rename"
    bl_options = {'REGISTER', 'UNDO'}

    from_collection: StringProperty(
        name="From Collection",
        default="high_poly",
        description="Collection used as rename source"
    )

    to_collection: StringProperty(
        name="To Collection",
        default="low_poly",
        description="Collection that will be renamed"
    )

    name_from: StringProperty(
        name="Name From",
        default="_high",
        description="Substring removed from source object name"
    )

    name_to: StringProperty(
        name="Name To",
        default="_low",
        description="Substring appended to renamed objects"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        from_col = bpy.data.collections.get(self.from_collection)
        to_col = bpy.data.collections.get(self.to_collection)

        if not from_col or not to_col:
            self.report({'ERROR'}, "One or both collections not found")
            return {'CANCELLED'}

        selected = set(context.selected_objects)

        # Selected source objects (FROM COLLECTION)
        source_objects = []
        for obj in from_col.objects:
            if (
                obj.type == 'MESH'
                and obj in selected
            ):
                source_objects.append({
                    "obj": obj,
                    "center": bbox_center_world(obj),
                    "used": False
                })


        # Selected target objects (TO COLLECTION)
        for target_obj in to_col.objects:
            if (
                target_obj.type != 'MESH'
                or target_obj not in selected
            ):
                continue

            target_center = bbox_center_world(target_obj)

            best_match = None
            best_distance = float('inf')

            for src in source_objects:
                if src["used"]:
                    continue

                dist = (src["center"] - target_center).length
                if dist < best_distance:
                    best_distance = dist
                    best_match = src

            if best_match:
                base_name = best_match["obj"].name.replace(self.name_from, "")
                target_obj.name = base_name + self.name_to
                best_match["used"] = True

        self.report({'INFO'}, "BBox batch rename complete (selected only)")
        return {'FINISHED'}


# MENU HOOK (IMPORTANTE!)

def menu_func(self, context):
    self.layout.operator(
        TK_OT_bbox_batch_rename.bl_idname,
        text="BBox Batch Rename"
    )

# REGISTER/UNREGISTER:
classes = (
    TK_OT_bbox_batch_rename,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
