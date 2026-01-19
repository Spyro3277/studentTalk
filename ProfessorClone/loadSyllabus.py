from pypdf import PdfReader
from typing import List, Union
from pypdf.generic import Destination




reader = PdfReader("test.pdf")
outfile = "output.txt"


#Prints all the pages in the pdf as a .txt file. This is needed to split the text by heading
amountOfPages = reader.get_num_pages()
pagesRead = 0
while True:
    page = reader.pages[pagesRead]
    #print(page.extract_text(extraction_mode="layout") + "\n")
    with open(outfile, 'a') as file:
        file.write(page.extract_text())

    pagesRead += 1

    if pagesRead == amountOfPages:
        break


#Prints the nested outlines
nestedOutlines = []
def print_outline(
    outlines: List[Union[Destination, List[Destination]]],
    reader: PdfReader,
    level: int = 0
) -> None:
    #Prints all the outlines and sub-outlines
    for item in outlines:
        if isinstance(item, list):
            # Recursively handle the nested list of children
            print_outline(item, reader, level + 1)
        else:
            page_number = reader.get_destination_page_number(item)
            
            indent = "  " * level

            if page_number is None:
                #print(f"{indent}- {item.title} (No page destination)")
                nestedOutlines.append(item.title)
            else:
                #print(f"{indent}- {item.title} (Page {page_number + 1})")
                nestedOutlines.append(item.title)





#print("Nested Outline Hierarchy:")
#print("-" * 25)

print_outline(reader.outline, reader)

data = []

with open(outfile, 'r') as file:
    currentHeading = None
    currentSection = []
    for line in file:
        line = line.strip()

        if line in nestedOutlines:
           if currentHeading is not None:
               data.append([currentHeading, " ".join(currentSection)])
           currentHeading = line
           currentSection = []
           
        else:
           if line:
               currentSection.append(line)

if currentHeading is not None:
    data.append([currentHeading, " ".join(currentSection)])

print(data)
            

#Clears the created txt file 
with open(outfile, 'w') as file:
    pass




