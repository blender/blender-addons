
print(30*"+")
import bpy
if not hasattr(bpy.context.scene, "matlib_categories"):
	class EmptyProps(bpy.types.PropertyGroup):
		pass
	bpy.utils.register_class(EmptyProps)
	bpy.types.Scene.matlib_categories = bpy.props.CollectionProperty(type=EmptyProps)
cats = bpy.context.scene.matlib_categories
for cat in cats:
	cats.remove(0)

cat = cats.add()
cat.name = "Colors" 
cat = cats.add()
cat.name = "Nature" 
cat = cats.add()
cat.name = "Woods" 
bpy.ops.wm.save_mainfile(filepath="D:\\Blender Foundation\\Blender\\2.73\\scripts\\addons\\matlib\\Otherlib.blend", check_existing=False, compress=True)