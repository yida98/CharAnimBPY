import bpy
from mathutils import Vector


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
        
    boneScale: bpy.props.FloatProperty(
        name = "Display Size",
        default = 0.02,
        soft_min = 0.0,
    )
        
    bboneSeg1: bpy.props.IntProperty(
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
    
    customDisplay: bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = "Display"
        )
        
    straightenHead: bpy.props.BoolProperty(
        name = "Move head",
        description = "Straighten head or tail",
        default = False
    )
    
    straightenAxis: bpy.props.EnumProperty(
        items = [("X", "+X", "Positive X axis", 1),
        ("Y", "+Y", "Positive Y axis", 2),
        ("Z", "+Z", "Positive Z axis", 3),
        ("nX", "-X", "Negative X axis", 4),
        ("nY", "-Y", "Negative Y axis", 5),
        ("nZ", "-Z", "Negative Z axis", 6)
        ],
        name = "Axis",
        default = 1
    )
    
    customDisplay1: bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = "Display"
        )
        
class GeneralSettings(bpy.types.PropertyGroup):
    newName: bpy.props.StringProperty(
        name = "Name",
        description = "Rename some items to a new name"
        )
        
        
# ------------------------
# OPERATORS
# ------------------------

def createBoneAt(location, armature, name = "Bone", length = 0.5, roll = 0, normal = Vector((0,0,1))):
    
    currBone = armature.data.edit_bones.new(name = name)
    currBone.head = location
    currBone.tail = location + (length * normal)
    currBone.roll = roll
    
    return currBone

def deselectBone(bone):
    bone.select_head = False
    bone.select_tail = False
    bone.select = False
    return bone


class RenameItems(bpy.types.Operator):
    bl_idname = "bone.rename_all"
    bl_label = "Rename All"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        context.view_layer.update()
        myTool = bpy.context.scene.general_tool
        rename = myTool.newName
        
        activeObj = context.active_object
        
        if activeObj.mode == 'OBJECT':
            for item in context.selected_objects:
                item.name = rename
        elif activeObj.type == 'ARMATURE':
            if activeObj.mode == 'EDIT':
                for bone in context.selected_bones:
                    bone.name = rename
            elif activeObj.mode == 'POSE':
                for bone in context.selected_pose_bones:
                    bone.name = rename
            
        return {'FINISHED'}

class AddBones(bpy.types.Operator):
    bl_idname = "bone.add_bone"
    bl_label = "Add Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    def createBonesAt(self, context, vec):
        armature = bpy.data.objects[0]
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                armature = obj
        
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
            
            currBone = createBoneAt(v, armature)
            myTool = bpy.context.scene.bone_tool
            
            if myTool.bbone:
                # Add bends
                currBone.bbone_segments = myTool.bboneSeg
            
            if myTool.switchDir:
                # Switch bone direction
                bpy.ops.armature.switch_direction()
            
            # Scale down
            
            scale = myTool.boneScale
            currBone.bbone_x = scale
            currBone.bbone_z = scale
                
    @classmethod
    def poll(cls, context):
        if len(bpy.data.objects) > 0:
            activeObj = context.active_object
            objs = context.selected_objects
            if activeObj.type == 'MESH' and len(objs) == 2:
                for obj in objs:
                    if obj != activeObj and obj.type == 'ARMATURE':
                        activeObj.update_from_editmode()
                        for v in activeObj.data.vertices:
                            if v.select:
                                return True
        return False
    
    def execute(self, context):
    
        obj = context.object
        obj.update_from_editmode()
        selected = [(obj.matrix_world @ v.co) for v in obj.data.vertices if v.select] 
        
        self.createBonesAt(context, selected)
        return {'FINISHED'}
    
class CopyConstraints(bpy.types.Operator):
    bl_idname = "bone.copy_constraints"
    bl_label = "Copy All"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'POSE' and len(context.selected_pose_bones) > 1:
            return True
        return False
    
    def execute(self, context):
        
        activeBoneConstraints = context.active_pose_bone.constraints
        
        for bone in bpy.context.selected_pose_bones:
            if bone != context.active_pose_bone:
                for constraint in context.active_pose_bone.constraints:
                    bone.constraints.copy(constraint)
                
        return {'FINISHED'}
    
class DeleteConstraints(bpy.types.Operator):
    bl_idname = "bone.delete_constraints"
    bl_label = "Delete All"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'POSE' and len(context.selected_pose_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        
        for bone in bpy.context.selected_pose_bones:
            for constraint in bone.constraints:
                bone.constraints.remove(constraint)
                
        return {'FINISHED'}
        
class DeformOn(bpy.types.Operator):
    bl_idname = "bone.deform_on"
    bl_label = "On"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'EDIT' and len(context.selected_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        
        for bone in bpy.context.selected_bones:
            bone.use_deform = True
                
        return {'FINISHED'}
    
class DeformOff(bpy.types.Operator):
    bl_idname = "bone.deform_off"
    bl_label = "Off"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'EDIT' and len(context.selected_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        
        for bone in bpy.context.selected_bones:
            bone.use_deform = False
                
        return {'FINISHED'}
    
class BatchSeg(bpy.types.Operator):
    bl_idname = "bone.add_bend"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'EDIT' and len(context.selected_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        
        myTool = context.scene.bone_tool
        
        for bone in bpy.context.selected_bones:
            bone.bbone_segments = myTool.bboneSeg1
        
        return {'FINISHED'}
    
class ControlBones(bpy.types.Operator):
    bl_idname = "bone.control_bones"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'EDIT' and len(context.selected_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        bpy.context.view_layer.update()
        obj = context.object
        armature = bpy.data.armatures[obj.name]
        myTool = context.scene.bone_tool
        selectedBones = list(map(lambda a: a.name , list(bpy.context.selected_bones)))
        
        self.report({'INFO'}, "STARTLoB: %s" % (list(selectedBones)))
        for boneName in selectedBones:
            bpy.context.view_layer.update()
            
            self.report({'INFO'}, "1LoB: %s" % (boneName))
            bone = armature.edit_bones[boneName]
            normal = (bone.tail - bone.head).normalized()
            
            head = bone.head - (0.1 * normal)
            tail = bone.tail
            bone.parent = None
            self.report({'INFO'}, "head: %s, tail: %s, normal: %s" % (head, tail, normal))
#            bone.bbone_easein = 0
#            bone.bbone_easeout = 0
            
#            bone.bbone_handle_type_start = 'ABSOLUTE'
#            bone.bbone_handle_type_end = 'ABSOLUTE'
            
#            deselectBone(bone)
            
            # Add bones head and tail 
            
            ctrlLocs = [head, tail]
            basename = "HNDL_" + boneName
            if "_" in boneName:
                basename = "HNDL_" + boneName.split("_", 1)[1]
            
            for i in range(len(ctrlLocs)):
                currBone = createBoneAt(ctrlLocs[i], obj, basename, 0.1, 0, normal)
                self.report({'INFO'}, "loc: %s, name: %s" % (ctrlLocs[i], currBone.name))
                currBoneName = currBone.name
                currBone.use_deform = False
                
                if i == 0:
                    bone = armature.edit_bones[boneName]
                    bone.parent = currBone
                    bone.use_connect = False

#                    bone.bbone_custom_handle_start = currBone
                else:
                    bpy.ops.object.mode_set(mode = 'POSE')
                    poseBone = context.object.pose.bones[boneName]
                    poseBone.constraints.new(type="STRETCH_TO").target = obj
                    poseBone.constraints["Stretch To"].subtarget = currBoneName
                    
#                    bone.bbone_custom_handle_end = currBone
                    
                    bpy.ops.object.mode_set(mode = 'EDIT')
                
                if myTool.customDisplay:
                    bpy.ops.object.mode_set(mode = 'POSE')
                    poseBone = context.object.pose.bones[currBoneName]
                    poseBone.custom_shape = myTool.customDisplay
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    
        
        return {'FINISHED'}
    
class StraightenNormal(bpy.types.Operator):
    bl_idname = "bone.straighten"
    bl_label = "Straighten"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'EDIT' and len(context.selected_bones) > 0:
            return True
        return False
    
    def execute(self, context):
               
        obj = context.object
        armature = bpy.data.armatures[obj.name]
        myTool = context.scene.bone_tool
        
        head = myTool.straightenHead
        
        for bone in context.selected_bones:
            len = bone.length
            map = {"X": Vector((len, 0, 0)),
               "Y": Vector((0, len, 0)), 
               "Z": Vector((0, 0, len)),
               "nX": Vector((-len, 0, 0)),
               "nY": Vector((0, -len, 0)),
               "nZ": Vector((0, 0, -len))
               }
        
            normal = map[myTool.straightenAxis]
            if head:
                origin = bone.tail
                newVector = origin + normal 
                bone.head = newVector
            else:
                origin = bone.head
                newVector = origin + normal
                bone.tail = newVector
            
            bone.roll = 0
        
        return {'FINISHED'}
    
class ChangeDisplay(bpy.types.Operator):
    bl_idname = "bone.change_display"
    bl_label = "Change"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode == 'POSE' and len(context.selected_pose_bones) > 0:
            return True
        return False
    
    def execute(self, context):
        
        myTool = context.scene.bone_tool
        
        newImage = myTool.customDisplay1
        
        for bone in context.selected_pose_bones:
            bone.custom_shape = newImage
        
        return {'FINISHED'}
    

# ------------------------
# PANELS
# ------------------------
    
class GeneralPanel(bpy.types.Panel):
    bl_label = "General"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tools"
    
    def draw(self, context):
        layout = self.layout
        
        myTool = context.scene.general_tool
        
        row = layout.row()
        row.label(text = "Batch Rename", icon = 'SORTALPHA')
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
        activeObj = context.active_object
        
        row = layout.row()
        
        if activeObj.mode == 'EDIT':
            row.label(text = "Add Bones", icon = 'GROUP_BONE')
            row = layout.row()
            row.prop(myTool, "bbone")
            row = layout.row()
            row.prop(myTool, "switchDir")
            row = layout.row()
            row.prop(myTool, "bboneSeg")
            row = layout.row()
            row.prop(myTool, "boneScale")
            row = layout.row()
            row.operator("bone.add_bone")
            
        row = layout.row()
        
        if activeObj.type == 'ARMATURE':
            if activeObj.mode == 'POSE':
                row.label(text = "Bone Constraints", icon = 'CONSTRAINT_BONE')
                row = layout.row()
                row.operator("bone.delete_constraints")
                row.operator("bone.copy_constraints")
                
                row = layout.row()
                row.label(text = "Batch change display", icon = 'MODIFIER_DATA')
                row = layout.row()
                row.prop(myTool, "customDisplay1")
                row = layout.row()
                row.operator("bone.change_display")            
                
            elif activeObj.mode == 'EDIT':
                
                row = layout.row()
                row.label(text = "Add Control Bones", icon = 'BONE_DATA')
                row = layout.row()
                row.prop(myTool, "customDisplay")
                row = layout.row()
                row.operator("bone.control_bones")
                
                row = layout.row()
                split = layout.split(factor = 0.5)
                col1 = split.column()
                col1.label(text = "Deform", icon = 'BONE_DATA')
                col2 = split.column()
                col3 = split.column()
                col2.operator("bone.deform_on")
                col3.operator("bone.deform_off")
                
                row = layout.row()
                row = layout.row()
                row.label(text = "Batch Bone Segmentation", icon = 'BONE_DATA')
                
                split = layout.split(factor = 0.7)
                col1 = split.column()
                col2 = split.column()
                col1.prop(myTool, "bboneSeg1")
                col2.operator("bone.add_bend")
                
                row = layout.row()
                row.label(text = "Straighten Bones", icon = "NORMALS_FACE")
                row = layout.row()
                row.prop(myTool, "straightenHead")
                row.prop(myTool, "straightenAxis")
                row = layout.row()
                row.operator("bone.straighten")
        
        
# ------------------------
# REGISTER
# ------------------------
            
classes = (BoneSettings, GeneralSettings, AddBones, RenameItems, CopyConstraints, DeleteConstraints, DeformOn, DeformOff, BatchSeg, ControlBones, StraightenNormal, ChangeDisplay, GeneralPanel, OperatorPanel)

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