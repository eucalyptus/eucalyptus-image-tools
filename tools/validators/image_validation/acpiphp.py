from image_validation import ImageAccess

def validator(image=False, libguestfs=False, fuse=False, trace=False):
    val = ImageAccess(image, libguestfs, fuse, trace)
