fetch("/showAllFolders")
.then(res => res.json())
.then(folders =>{
    const select = document.getElementById("folderSelect");
    select.innerHTML = '<option value="">--Select a Class--</option>';

    folders.forEach(folder =>{
        const option = document.createElement("option");
        option.value = folder;
        option.textContent = folder;
        select.appendChild(option);
    });
})
.catch(err => console.error(err));

async function loadFolder(params){
    const select = document.getElementById("folderSelect");
    const classFolderName = select.value;

    try{
        const res = await fetch(`/loadClassContent/${encodeURIComponent(classFolderName)}`,{
            method: "POST"
        });

    }
    catch(err){
        console.error(err);
    }
}