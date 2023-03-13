import pprint, argparse
from pypdf import PdfWriter, PdfReader, Transformation, PaperSize



pp=pprint.PrettyPrinter()

inputfile="input.pdf"
hfolds=3
vfolds=2

sidespersection=2**hfolds*2**vfolds

reader = PdfReader(inputfile)

pages=len(reader.pages)
sidespersection=9


# Specification. First we work out the section sizes by working out how many
# pages are in a sheet.

def horizontal_unfold(book):
    #print("hsplit")
    pages=book['pages']
    new_width=book['width']*2
    half_length = len(pages[0][0])//2
    rowpages=[]
    newpages=[]
    for i in range(new_width):
        rowpages.append([])

    for i in range(book['height']):
        for j in range(book['width']):
            #print(f"i: {i}, j: {j}, half_length = {half_length}, new_width={new_width}")
            rowpages[new_width-1-j] = pages[i][j][:half_length]
            rowpages[j] = pages[i][j][half_length:]
            rowpages[new_width-1-j].reverse()

        newpages.append(rowpages.copy())

    newbook =  { 
        'height': book['height'], 
        'width': new_width, 
        'pages': newpages 
    }
    return newbook

def flip(n):
    return 1-n

def vertical_unfold(book):
    # Unfold top to bottom so double the height.
    #print("vsplit")
    #pp.pprint(book)
    pages=book['pages']
    new_height=book['height']*2
    half_length = len(pages[0][0])//2
    newpages=[]
    for i in range(new_height):
        newpages.append([])

    for i in range(book['height']):
        row1pages=[]
        row2pages=[]
        for j in range(book['width']):
            #print(f"i: {i}, j: {j}, half_length: {half_length}")
            row2pages.append(pages[i][j][:half_length])
            #pp.pprint(row2pages)
            row1pages.append(pages[i][j][half_length:])
            row2pages[j].reverse()
            for d in row2pages[j]:
                d['up'] = 1 - d['up']


        newpages[i]=row1pages.copy()
        newpages[new_height-1-i]=row2pages.copy()

    newbook =  { 
        'height': new_height, 
        'width': book['width'], 
        'pages': newpages 
    }
    return newbook

#
def flip_and_split(book):
    # The pages are on the back of the paper but their positions
    # are listed from the front. So we need to flip the positions
    # to get the correct printing order.
    # There are two pages one after the other in each row. They need #
    # to be split into extra columns.
    # So if we have:
    # [[[2, 1], [15, 16], [14, 13], [3, 4]],
    #  [[7, 8], [10, 9],  [11, 12], [6, 5]]],
    # We need to get to:
    # [[[16, 15], [1, 2]]
    #  [[ 9, 10], [8, 7]]
    #  [[ 4,  3], [13,14]
    #  [[ 5,  6], [12,11]]
    #
    #pp.pprint(book)
    front=[]
    back=[]
    width=book['width']//2

    for i in range(book['height']):
        frontline=[]
        backline=[]
        flatwidth = [element for innerList in book['pages'][i] for element in innerList]
        #pp.pprint(flatwidth)

        for j in range(width):
            #print(f"width: {width}, i={i}, j={j}")
            frontline.append(flatwidth[width-j-1])
            backline.append(flatwidth[width*2-j-1])
        #pp.pprint(frontline)
        #pp.pprint(backline)
        front.append(frontline)
        #print('Front')
        #pp.pprint(front)
        back.append(backline)
    newbook=front+back
    return newbook


#           123      32              3        2
def info(pages, sides_per_section, hfolds, vfolds):
    bookinfo={}
    if hfolds > vfolds+1 or hfolds < vfolds - 1:
        print("Folds must only be one different.")
        exit(9)
    sides_per_print_page = 2**(hfolds+vfolds)
    print(f"Calculated sides per sheet = {sides_per_print_page}")
    calculated_sides_per_section = sides_per_print_page * (
            (sides_per_section//sides_per_print_page) +
            (sides_per_section%sides_per_print_page > 0)
        )
    print(f" Requested sides per section = {sides_per_section}")
    print(f"Calculated sides per section = {calculated_sides_per_section}")
    calculated_sides = calculated_sides_per_section * (
            (pages//calculated_sides_per_section) +
            (pages%calculated_sides_per_section > 0)
        )
    print_sides = (calculated_sides//sides_per_print_page)
    assert 0 == (calculated_sides%sides_per_print_page)
    print(f" Requested pages = {pages}")
    print(f"Calculated sides = {calculated_sides}")
    print(f"Calculated print sheets = {print_sides}")
    bookinfo['sides_per_sheet'] = sides_per_print_page
    bookinfo['sides_per_section'] = calculated_sides_per_section
    bookinfo['sheets'] = print_sides
    bookinfo['hfolds'] = hfolds
    bookinfo['vfolds'] = vfolds
    bookinfo['pages'] = pages
    return bookinfo
    
def unfold(bookinfo):
    # Create a sequence with the number of pages per section
    section_page_list = list(range(1,bookinfo['sides_per_section']+1))
    section_page_list.reverse()
    pagedict=[]
    for i in section_page_list:
        pagedict.append({'pg': i, 'up':0 })
    book = { 'height': 1, 'width': 1, 'pages': [[ pagedict, ]] }

    # Unfold here.
    hfolds_left = bookinfo['hfolds']
    vfolds_left = bookinfo['vfolds']

    if hfolds_left >= vfolds_left:
        next_unfold = 'h'
    else:
        next_unfold = 'v'

    while (hfolds_left > 0 or vfolds_left > 0):
        #print(f"Hfolds left: {hfolds_left}, vfolds left: {vfolds_left}")
        if next_unfold == 'h':
            book = horizontal_unfold(book)
            next_unfold = 'v'
            hfolds_left-=1
        else:
            book = vertical_unfold(book)
            next_unfold = 'h'
            vfolds_left-=1

    assert vfolds_left == 0
    assert hfolds_left == 0
    #pp.pprint(book)
    book=flip_and_split(book)
    return book

def create_impose_plan(bookinfo, section):
    # This is currently hardcoded to A4, and doesn't seem to work.
    page_width=595
    page_height=842

    pages_across = 2**(hfolds-1)
    pages_down = 2**vfolds

    scale_factor = 1/max(pages_across, pages_down)

    outfile=f"""$PageWidth = {page_width}
$PageHeight = {page_height}
$ScaleFactor = {scale_factor}"""
    for sheet in range(bookinfo['sheets']):
        for j, row in enumerate(section):
            for i, p in enumerate(row):
                #print(f"Sheet: {sheet}, j: {j}, i: {i}")
                page_in_section = (j*pages_across) + i
                in_page=p['pg']+(sheet*bookinfo['sides_per_section'])
                out_page = 1 + sheet * 2 + page_in_section*2//bookinfo['sides_per_section']
                rotation = p['up'] * 180
                xpos=i*(page_width/pages_across)
                ypos=(j%pages_down)*(page_height/pages_down)
                if in_page <= pages:
                    outfile+=f"\n{in_page}; {out_page}; {rotation}; {xpos}; {ypos};"
    return outfile

def arrange_pdf(bookinfo, section, reader):
    writer=PdfWriter()
    pages_across = 2**(bookinfo['hfolds']-1)
    pages_down = 2**bookinfo['vfolds']
    scale_factor = 1/max(pages_across, pages_down)
    for sheet in range(bookinfo['sheets']):
        for j, row in enumerate(section):
            for i, p in enumerate(row):
                #print(f"Sheet: {sheet}, j: {j}, i: {i}")
                page_in_section = (j*pages_across) + i
                if (2*page_in_section)%bookinfo['sides_per_section'] == 0:
                    destpage = writer.add_blank_page(
                        width=PaperSize.A4.width, height=PaperSize.A4.height)
                    print('#',end='',flush=True)
                in_page=p['pg']+(sheet*bookinfo['sides_per_section'])
                out_page = 1 + sheet * 2 + page_in_section*2//bookinfo['sides_per_section']
                rotation = p['up'] * 180
                xpos=i*(PaperSize.A4.width)+p['up']*PaperSize.A4.width
                ypos=((pages_down-1)-j%pages_down)*(PaperSize.A4.height)+p['up']*PaperSize.A4.height
                #print(f"in_page: {in_page}, xpos: {xpos}, ypos: {ypos}, scale: {scale_factor}, rotation: {rotation}")
                if in_page <= bookinfo['pages']:
                    sourcepage=reader.pages[in_page-1]
                    destpage.merge_transformed_page(
                        sourcepage,
                        Transformation(
                        ).rotate(
                            rotation
                        ).translate(
                            xpos,
                            ypos,
                        ).scale(
                            sx=scale_factor,
                            sy=scale_factor

                        ),
                    )
    print('#')
    with open("imposed.pdf","wb") as fp:
        writer.write(fp)


bookinfo=info(pages, sidespersection, hfolds, vfolds)
section=unfold(bookinfo)
#pp.pprint(bookinfo)
#impose_plan=create_impose_plan(bookinfo, section)
arrange_pdf(bookinfo,section,reader)

with open('impose_plan', 'w', encoding='utf-8') as f:
    f.write(impose_plan)
#print(impose_plan)
