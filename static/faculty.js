
async function addToClassFolder(params){
    console.log("Function triggered");
    const fileInput = document.getElementById("assignmentFile");
    const uploadStatus = document.getElementById("uploadAssignmentStatus");
    const select = document.getElementById("folderSelect");
    const classFolderName = select.value;

     if (!fileInput.files.length){
        uploadStatus.textContent = "Choose a file first";
        return;
    }
const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file)


    try{
        console.log("Sending request to:", `/addToClassFolder/${classFolderName}`);
        const res = await fetch(`/addToClassFolder/${encodeURIComponent(classFolderName)}`,
        {
            method: "POST",
            body: formData
        }
    );

    const data = await res.json();
    uploadStatus.textContent = data.message || data.error;
}catch(err){
    uploadStatus.textContent = "Failed Upload: " + err.message;
} 

}

async function addNewCourse(params){
    const newCourseName = document.getElementById("newCourseName").value;
    try{
        const res = await fetch(`/addNewClass/${encodeURIComponent(newCourseName)}`,
        {
            method: "POST",
        }
    );
    }catch(err){
        console.log(err);
    }
}