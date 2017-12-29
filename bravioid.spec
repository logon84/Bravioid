# -*- mode: python -*-
import os
import site

typelib_path = os.path.join(site.getsitepackages()[1], 'gnome', 'lib', 'girepository-1.0')

block_cipher = None


a = Analysis(['bravioid.py'],
             pathex=['E:\\GUI'],
             binaries=[(os.path.join(typelib_path, tl), 'gi_typelibs') for tl in os.listdir(typelib_path)],
             datas=[('bravioid.glade', '.'), ('res/*.png', 'res' ) ],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='bravioid',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
