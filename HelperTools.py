import bpy

# ------------------------
# PROPERTY GROUPS
# ------------------------
class BoneSettings(bpy.types.PropertyGroup):
    bbone: bpy.props.BoolProperty(
        name = "Bendy Bone",
        description = "Choose to create bbone or regular",
        default = False
        )
        
    bboneSeg: bpy.props.IntProperty(
        name = "Segments",
        description = "Bendy Segments",
        default = 4,
        soft_min = 0,
        soft_max = 36
        )
    
    switchDir: bpy.props.BoolProperty(
        name = "Switch Direction",
        description = "Switch the tail and head location of the bone",
        default = False
        )
        
class GeneralSettings(bpy.types.PropertyGroup):
    newName: bpy.props.StringProperty(
        name = "Name",
        description = "Rename some items to a new name"
        )
        
# ------------------------
# OPERATORS
# ------------------------
class RenameItems(bpy.types.Operator):
    bl_idname = "bone.rename_all"
    bl_label = "Rename All"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        myTool = bpy.context.scene.general_tool
        rename = myTool.newName
        
        activeObj = context.active_object
        
        if activeObj.mode == 'OBJECT':
            for item in context.selected_objects:
                item.name = rename
        else:
            if activeObj.type == 'ARMATURE':
                for bone in context.selected_bones:
                    bone.name = rename
            
        return {'FINISHED'}

class AddBones(bpy.types.Operator):
    bl_idname = "bone.add_bone"
    bl_label = "Add Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    def createBonesAt(self, context, vec):
        armature = bpy.data.objects['Armature.001']
        
        # Go to object mode
        if context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
        
        # Deselect everything but armature
        for object in context.selected_objects:
            object.select_set(False)
        armature.select_set(True)
        context.view_layer.objects.active = armature
        
        # Set Armature into 'EDIT' mode
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        # Iterate through the given vectors and create a BBone at each Vertices
        for v in vec:
            context.scene.cursor.location = v
            
            # Add bbone
            bpy.ops.armature.bone_primitive_add()
            
            bpy.ops.armature.select_linked()
            currBone = context.selected_bones[0]
            myTool = bpy.context.scene.bone_tool
            
            if myTool.bbone:
                # Add bends
                currBone.bbone_segments = myTool.bboneSeg
            
            if myTool.switchDir:
                # Switch bone direction
                bpy.ops.armature.switch_direction()
            
            # Scale down
            scale = 0.02
            currBone.bbone_x = scale
            currBone.bbone_z = scale
                
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'MESH':
            obj.update_from_editmode()
            for v in obj.data.vertices:
                if v.select:
                    return True
        return False
    
    def execute(self, context):
    
        obj = context.object
        obj.update_from_editmode()
        selected = [(obj.matrix_world @ v.co) for v in obj.data.vertices if v.select] 
        
        self.createBonesAt(context, selected)
        return {'FINISHED'}
    
class GeneralPanel(bpy.types.Panel):
    bl_label = "General"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tools"
    
    def draw(self, context):
        layout = self.layout
        
        myTool = context.scene.general_tool
        
        row = layout.row()
        row.prop(myTool, "newName")
        row = layout.row()
        row.operator("bone.rename_all")
        
        
        
class OperatorPanel(bpy.types.Panel):
    bl_label = "Bone Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tools"
    
    def draw(self, context):
        layout = self.layout
        
        myTool = context.scene.bone_tool
        row = layout.row()
        if context.active_object.mode == 'EDIT':
#            row.label(text = "Add Bones", icon = 'CUBE')
#            row = layout.row()
            row.prop(myTool, "bbone")
            row = layout.row()
            row.prop(myTool, "switchDir")
            row = layout.row()
            row.prop(myTool, "bboneSeg")
            row = layout.row()
            row.operator("bone.add_bone")
        
        
        
            
classes = (BoneSettings, GeneralSettings, AddBones, RenameItems, GeneralPanel, OperatorPanel)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.bone_tool = bpy.props.PointerProperty(type = BoneSettings)
    bpy.types.Scene.general_tool = bpy.props.PointerProperty(type = GeneralSettings)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.bone_tool
    del bpy.types.Scene.general_tool

if __name__ == "__main__":
    register()