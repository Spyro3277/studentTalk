#Prints all the top-level outlines in a pdf
topLevelOutlines = []
#print("Top-level outlines:")
#print("-" * 32)

for outline in reader.outline:
    if isinstance(outline, list):
        continue
    page_number = reader.get_destination_page_number(outline)

    if page_number is None:
        #print(f"{outline.title} -> No page destination")
        topLevelOutlines.append(outline.title)
    else:
        #print(f"{outline.title} -> page {page_number + 1}")
        topLevelOutlines.append(outline.title)