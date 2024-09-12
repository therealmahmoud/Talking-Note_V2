let modal;

/**
 * This function initializes the event listeners for the note-taking application.
 * It sets up the click events for the add note button, close button, outside click,
 * form submission, and AI chat button. It also calls the fetchNotes function to
 * retrieve and display existing notes.
 */
$(document).ready(function () {
  // Initialize the modal element
  modal = $("#noteModal");

  // Initialize the add note button, close button, and AI chat button
  var btn = $(".add-note-btn");
  var closeBtn = $(".close-btn");
  var sendBtn = $(".send-btn");

  // Add click event listener for AI chat button
  sendBtn.on("click", ai_chat);

  // Add click event listener for add note button
  btn.on("click", openModal);

  // Add click event listener for close button
  closeBtn.on("click", closeModal);

  // Add click event listener for outside click
  $(window).on("click", outsideClick);

  // Add click event listener for form submission
  $("#noteForm").on("submit", addNote);

  // Call fetchNotes function to retrieve and display existing notes
  fetchNotes();
});

/**
 * Fetches notes from the server and displays them in the UI.
 *
 * @returns {Promise<void>} - A promise that resolves when the notes are fetched and displayed.
 */
async function fetchNotes() {
  try {
    const response = await fetch("http://localhost:3000/notes");
    const notes = await response.json();
    const notesContainer = $("#notes-container");
    notesContainer.empty(); // Clear existing notes

	// Iterate over the notes and create a note element for each one
    notes.forEach((note) => {
      const noteElement = $(`
        <div class="note">
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
          <div class="note-title">${note.title}</div>
          <div class="note-content">${note.content}</div>
          <div class="note-actions">
            <span class="delete-note"><i class="fa fa-trash-o" style="font-size:30px" data-id="${note.notes_id}"></i></span>
          </div>
        </div>
      `);
      notesContainer.append(noteElement);
    });

    // Add event listeners to the delete icons
    $(".delete-note i").on("click", deleteNote);
  } catch (error) {
    console.error("Error fetching notes:", error);
  }
}

/**
 * Opens the modal for adding a new note.
 *
 * @function openModal
 * @returns {void} - This function does not return any value.
 *
 * @example
 * openModal();
 *
 * @see {@link closeModal} for closing the modal.
 * @see {@link fetchNotes} for fetching existing notes.
 * @see {@link addNote} for adding a new note.
 */
function openModal() {
  modal.show();
}

/**
 * Closes the modal for adding a new note.
 *
 * @function closeModal
 * @returns {void} - This function does not return any value.
 *
 * @example
 * closeModal();
 *
 * @see {@link openModal} for opening the modal.
 * @see {@link fetchNotes} for fetching existing notes.
 * @see {@link addNote} for adding a new note.
 */
function closeModal() {
	modal.hide();
  }
function closeModal() {
  modal.hide();
}

/**
 * Handles the click event for closing the modal when clicking outside of it.
 *
 * @param {Event} event - The click event object.
 * @returns {void} - This function does not return any value.
 *
 * @example
 * outsideClick(event);
 *
 * @see {@link openModal} for opening the modal.
 * @see {@link closeModal} for closing the modal.
 */
function outsideClick(event) {
  if ($(event.target).is(modal)) {
    modal.hide();
  }
}

/**
 * Handles the form submission event for adding a new note.
 *
 * @function addNote
 * @param {Event} event - The form submission event object.
 * @returns {Promise<void>} - A promise that resolves when the note is added successfully.
 *
 * @example
 * addNote(event);
 *
 * @see {@link fetchNotes} for fetching existing notes.
 * @see {@link closeModal} for closing the modal.
 */
async function addNote(event) {
  event.preventDefault();
  const noteTitle = $("#noteTitle").val();
  const noteContent = $("#noteContent").val();

  try {
    const response = await fetch("http://localhost:3000/notes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: noteTitle,
        content: noteContent,
      }),
    });

    if (response.ok) {
      fetchNotes(); // Refresh notes
      closeModal(); // Close modal
    } else {
      console.error("Error adding note");
    }
  } catch (error) {
    console.error("Error adding note:", error);
  }
}

/**
 * Handles the click event for the AI chat button.
 * It sends a prompt to the AI server, fetches the response, and displays it in the chat section.
 *
 * @param {Event} event - The click event object.
 * @returns {Promise<void>} - A promise that resolves when the AI response is received and displayed.
 *
 * @example
 * ai_chat(event);
 *
 * @see {@link fetchNotes} for fetching existing notes.
 * @see {@link addNote} for adding a new note.
 * @see {@link deleteNote} for deleting a note.
 */
async function ai_chat(event) {
  event.preventDefault();
  const prompt = $(".chat-input").val();
  const chatContainer = $(".chat-section");
  try {
    const response = await fetch("http://localhost:3000/notes/ai", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: prompt,
        }),
    });
    if (response.ok) {
      const data = await response.json();
      const chatElement = $(`
          <div class="chat-message">
              <div class="message"><h5>You:</h5> ${prompt}</div>
          </div>
          <div class="chat-message">
              <div class="message"><h5>AI:</h5> ${data.AI}</div>
          </div>
      `);
    chatContainer.append(chatElement);
    } else {
      console.error("Error fetching from AI");
    }
  } catch (error) {
    console.error("Error getting response", error);
  }  
}

/**
 * Deletes a note from the server and refreshes the notes list.
 *
 * @function deleteNote
 * @param {Event} event - The click event object.
 * @returns {Promise<void>} - A promise that resolves when the note is deleted successfully.
 *
 * @example
 * deleteNote(event);
 *
 * @see {@link fetchNotes} for fetching existing notes.
 * @see {@link addNote} for adding a new note.
 * @see {@link ai_chat} for handling AI chat functionality.
 */
async function deleteNote(event) {
  const noteId = $(event.target).data("id");

  try {
    const response = await fetch(`http://localhost:3000/notes/${noteId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      fetchNotes(); // Refresh notes
    } else {
      console.error("Error deleting note");
    }
  } catch (error) {
    console.error("Error deleting note:", error);
  }
}
