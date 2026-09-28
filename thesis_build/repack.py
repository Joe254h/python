import zipfile, shutil, sys, os
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
names = [n for n in zin.namelist() if not n.endswith('/')]
first = '[Content_Types].xml'
order = [first] + [n for n in names if n != first]
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
    for n in order:
        data = zin.read(n)
        # mimetype-style: content types stored first, deflated is fine for OPC
        z.writestr(n, data)
zin.close()
print("repacked", dst, os.path.getsize(dst)//1024, "KB;", len(order), "entries; first =", order[0])
