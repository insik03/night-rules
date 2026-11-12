from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
DEST='/Game/ThirdParty/PolyHaven'
for name in ['SM_PH_DeskBody']+['SM_PH_Drawer'+str(i) for i in range(1,7)]:
 t=unreal.AssetImportTask();t.filename=str(ROOT/'Art/ThirdParty/PolyHaven/Prepared'/(name+'.fbx'));t.destination_path=DEST;t.automated=True;t.replace_existing=True;t.save=True
 opt=unreal.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False
 opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;t.options=opt
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
 mesh=unreal.load_asset(DEST+'/'+name)
 if not mesh:raise RuntimeError('Missing '+name)
 mesh.set_material(0,unreal.load_asset(DEST+'/M_PH_metal_office_desk_0'))
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
unreal.log('DRAWER_IMPORT_COMPLETE')
