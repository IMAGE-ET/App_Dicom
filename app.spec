# -*- mode: python -*-

block_cipher = None


a = Analysis(['app.py'],
             pathex=['/Users/reynald-mac/Documents/EI4/DATASIM/Projet/app_PyQt/App_Dicom'],
             binaries=[],
             datas=[('darkorange.stylesheet','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='app',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='app')
app = BUNDLE(coll,
             name='app.app',
             icon=None,
             bundle_identifier=None)
