import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps

# motivational meme parameters
class size_1024_1024:
    QUOTE_CHAR_LIMIT = 42
    FONT_SIZE = 50
    SPACING_SIDE = 120
    SPACING_TOP = 50
    SPACING_BOTTOM = 350
    SPACING_BETWEEN_IMAGE_AND_QUOTE = 50
    SPACING_BETWEEN_LINES = 15
    SPACING_BETWEEN_QUOTE_AND_SOURCE = 20

# 1 to the sides (3 calls)
class size_2048_1024:
    QUOTE_CHAR_LIMIT = 55
    FONT_SIZE = 70
    SPACING_SIDE = 70
    SPACING_TOP = 70
    SPACING_BOTTOM = 350
    SPACING_BETWEEN_IMAGE_AND_QUOTE = 80
    SPACING_BETWEEN_LINES = 15
    SPACING_BETWEEN_QUOTE_AND_SOURCE = 20

# 1 up & to the sides (9 calls)
class size_2048_2048:
    pass # too expensive

# 3 in all directions (46 calls)
class size_8192_8192:
    pass # too expensive

# 2 up, 4 to the sides (45 calls)
class size_10240_6144:
    pass # too expensive

motivational_meme_parameters = {
    (1024, 1024): size_1024_1024,
    (2048, 1024): size_2048_1024,
}

def generate_motivational_meme(image_path, quote, source):
    FONT = 'Libre_Baskerville/LibreBaskerville-Regular.ttf'
    
    image = Image.open(image_path)
    m, n = image.size
    print(f"m={m}, n={n}")
    param = motivational_meme_parameters[image.size]
    
    image = ImageOps.expand(image, border=3, fill='white')
    image = ImageOps.expand(
        image,
        border=(
            param.SPACING_SIDE,
            param.SPACING_TOP,
            param.SPACING_SIDE,
            param.SPACING_BOTTOM,
        )
    )

    draw = ImageDraw.Draw(image)
    font_quote = ImageFont.truetype(FONT, size=param.FONT_SIZE)
    font_source = ImageFont.truetype(FONT, size=2*param.FONT_SIZE//3)

    # draw quote below image
    space_between_quote_lines = 0
    for caption in textwrap.wrap(quote, width=param.QUOTE_CHAR_LIMIT):
        draw.text(
            (m//2 + param.SPACING_SIDE,
                 n + param.SPACING_TOP +
                 param.SPACING_BETWEEN_IMAGE_AND_QUOTE + space_between_quote_lines),
            caption,
            fill='white',
            font=font_quote,
            anchor='mm',
            # align='center',
        )
        _x1, y1, _x2, y2 = draw.textbbox(
            (m//2 + param.SPACING_SIDE,
                 n + param.SPACING_TOP +
                 param.SPACING_BETWEEN_IMAGE_AND_QUOTE + space_between_quote_lines),
            caption,
            font=font_quote,
        )
        space_between_quote_lines += (y2 - y1)
        space_between_quote_lines += param.SPACING_BETWEEN_LINES

    # draw source below quote
    draw.text(
        (m//2 + param.SPACING_SIDE,
             n + param.SPACING_TOP +
             param.SPACING_BETWEEN_IMAGE_AND_QUOTE + space_between_quote_lines +
             param.SPACING_BETWEEN_QUOTE_AND_SOURCE),
        source,
        fill='white',
        font=font_source,
        anchor='mm',
        # align='center',
    )

    return image

def roll_horizontally(im, delta):
    """Roll an image sideways."""
    xsize, ysize = im.size

    delta = delta % xsize
    if delta == 0:
        return im

    left = im.crop((0, 0, delta, ysize))
    right = im.crop((delta, 0, xsize, ysize))
    im.paste(left, (xsize - delta, 0, xsize, ysize))
    im.paste(right, (0, 0, xsize - delta, ysize))

    return im

def roll_vertically(im, delta):
    """Roll an image vertically."""
    xsize, ysize = im.size

    delta = delta % xsize
    if delta == 0:
        return im

    top = im.crop((0, 0, xsize, delta))
    bottom = im.crop((0, delta, xsize, ysize))
    im.paste(top, (0, ysize - delta, xsize, ysize))
    im.paste(bottom, (0, 0, xsize, ysize - delta))

    return im

def merge_horizontally(left_image, right_image, overlap=0, image_priority='right'):
    w = left_image.size[0] + right_image.size[0] - overlap
    h = max(left_image.size[1], right_image.size[1])
    merged_image = Image.new("RGBA", (w, h))

    if image_priority == 'right':
        merged_image.paste(left_image)
        merged_image.paste(right_image, (left_image.size[0] - overlap, 0))
    elif image_priority == 'left':
        raise NotImplementedError()
    else:
        raise ValueError(f"image_priority was {image_priority} but it must be 'left' or 'right'")

    return merged_image

def merge_horizontally_sequentially(image_paths, overlap=0, image_priority='right'):
    if not image_paths: return None
    if len(image_paths) == 1: return Image.open(image_paths[0])
    if image_priority == 'left': raise NotImplementedError()

    left = Image.open(image_paths[0])
    for image_path in image_paths[1:]:
        left = merge_horizontally(left, Image.open(image_path), overlap=overlap, image_priority='right')

    return left

def merge_vertically(top_image, bottom_image, overlap=0, image_priority='bottom'):
    w = max(top_image.size[0], bottom_image.size[0])
    h = top_image.size[1] + bottom_image.size[1] - overlap
    merged_image = Image.new("RGBA", (w, h))

    if image_priority == 'bottom':
        merged_image.paste(top_image)
        merged_image.paste(bottom_image, (0, top_image.size[1] - overlap))
    elif image_priority == 'top':
        raise NotImplementedError()
    else:
        raise ValueError(f"image_priority was {image_priority} but it must be 'top' or 'bottom'")

    return merged_image

# todo: test me
def merge_vertically_sequentially(image_paths, overlap=0, image_priority='bottom'):
    raise NotImplementedError("need to test before using!")

    if not image_paths: return None
    if len(image_paths) == 1: return Image.open(image_paths[0])
    if image_priority == 'top': raise NotImplementedError()

    top = Image.open(image_paths[0])
    for image_path in image_paths[1:]:
        top = merge_vertically(top, Image.open(image_path), overlap=overlap, image_priority='bottom')

    return top

def transparent_crop(image, crop):
    m, n = image.size
    area_to_keep = {
        'left': (m//2, 0, m, n),
        'right': (0, 0, m//2, n),
        'top': (0, n//2, m, n),
        'bottom': (0, 0, m, n//2),
    }

    image_alpha = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(image_alpha)
    draw.rectangle(area_to_keep[crop], fill=255)

    image_rgba = image.copy()
    image_rgba.putalpha(image_alpha)
    return image_rgba    

# test functions
if __name__ == "__main__":
    image = Image.open('test/size_1024_1024.jpg')
    m, n = image.size

    test_horizontally = roll_horizontally(image.copy(), m//2)
    test_horizontally.show()

    test_vertically = roll_vertically(image.copy(), m//2)
    test_vertically.show()

    test_merge_horizontally = merge_horizontally(
        test_horizontally.copy(), test_vertically.copy(), overlap=m//2)
    test_merge_horizontally.show()

    test_merge_vertically = merge_vertically(
        test_horizontally.copy(), test_vertically.copy(), overlap=n//2)
    test_merge_vertically.show()

    image = Image.open('test/size_1024_1024 (2).jpg')
    transparent_crop(image, 'left').show()
    transparent_crop(image, 'right').show()
    transparent_crop(image, 'top').show()
    transparent_crop(image, 'bottom').show()

    QUOTE = "Did ever people hear the voice of God speaking out of the midst of the fire, as thou hast heard, and live?"
    SOURCE = "Deuteronomy 4:33"

    image = generate_motivational_meme('test/size_1024_1024.jpg', QUOTE, SOURCE)
    image.show()

    image = generate_motivational_meme('test/size_2048_1024.png', QUOTE, SOURCE)
    image.show()
  