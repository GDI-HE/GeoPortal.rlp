function validatePassword(password) {
  const length = password.length >= 9;
  const lowercase = /[a-z]/.test(password);
  const uppercase = /[A-Z]/.test(password);
  const number = /\d/.test(password);
  return { length, lowercase, uppercase, number };
}

function updatePasswordStrength(passwordFieldSelector) {
  const password = $(passwordFieldSelector).val();
  const { length, lowercase, uppercase, number } = validatePassword(password);

  // Update UI elements based on password criteria individually
  $("#length").css("color", length ? "green" : "red");
  $("#lowercase").css("color", lowercase ? "green" : "red");
  $("#uppercase").css("color", uppercase ? "green" : "red");
  $("#number").css("color", number ? "green" : "red");

  $(passwordFieldSelector).css("border", (length && lowercase && uppercase && number) ? "" : "2px solid red");
}

// Event handler for password input
$("#password, #change_profile_password").on("input", function () {
  validatePasswordOnChange(`#${this.id}`);
  updatePasswordStrength(`#${this.id}`);
});

// Add a new function to handle password change and validation
function validatePasswordOnChange(selector) {
  const password = $(selector).val();
  const { length, lowercase, uppercase, number } = validatePassword(password);

  // Update UI elements based on password criteria individually
  $("#length").css("color", length ? "green" : "red");
  $("#lowercase").css("color", lowercase ? "green" : "red");
  $("#uppercase").css("color", uppercase ? "green" : "red");
  $("#number").css("color", number ? "green" : "red");
}

$(document).ready(function () {
  const hideElements = ["#password-rules", "#CheckPasswordMatch", "#CheckEmail"];
  hideElements.forEach(selector => $(selector).hide());

  const handleFocusBlur = (inputSelectors, messageSelector) => {
    $(inputSelectors).on('focus keyup', function () {
      $(messageSelector).toggle($(this).val().length > 0);
    });
  }

  handleFocusBlur("#password, #change_profile_password", "#password-rules");
  handleFocusBlur("#id_passwordconfirm, #change_profile_passwordconfirm", "#CheckPasswordMatch");
  handleFocusBlur("#email, #change_profile_email", "#CheckEmail");
});

let isPasswordValid = false;
let isUsernameValid = $("#username").val() !== "";

function checkPassword(password, confirmPassword) {
  const isMatch = password === confirmPassword;
  const isEmpty = !password && confirmPassword;
  const isError = !isMatch || isEmpty;
  const message = isError ? (isEmpty ? enterPasswordMessage : passwordsNotMatchMessage) : passwordsMatchMessage;
  const color = isError ? "red" : "green";
  const border = isError ? "2px solid red" : "";
  $("#CheckPasswordMatch").html(message).css("color", color);
  $("#id_passwordconfirm, #change_profile_passwordconfirm").css("border", border);
  if (isEmpty && isError) $("#password, #change_profile_password").css("border", "2px solid red");
}

$("form").on("input", function () {
  const username = $("#username"), oldPassword = $("#change_profile_oldpassword"), newPassword = $("#change_profile_password"), confirmPassword = $("#change_profile_passwordconfirm");
  username.css("border", username.val() !== "" ? "" : "2px solid red");
  const isPasswordValid = oldPassword.val() !== "" || (newPassword.val() !== "" && confirmPassword.val() !== "");
  oldPassword.css("border", isPasswordValid ? "" : "2px solid red");
});

$("#password, #id_passwordconfirm, #change_profile_password, #change_profile_passwordconfirm").on("input", function () {
  const password = $("#password").val() || $("#change_profile_password").val();
  const confirmPassword = $("#id_passwordconfirm").val() || $("#change_profile_passwordconfirm").val();
  checkPassword(password, confirmPassword);
});

$("#email, #change_profile_email").on("input", function () {
  const $this = $(this);
  const email = $this.val();
  const isChangeProfileEmail = $this.attr('id') === 'change_profile_email';
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const isValidEmail = emailRegex.test(email) && email !== "";
  const message = isValidEmail ? (isChangeProfileEmail ? ValidEmailMessageChange : ValidEmailMessage) : (isChangeProfileEmail ? enterValidMessageChange : enterValidEmailMessage);
  const color = isValidEmail ? "green" : "red";
  const border = isValidEmail ? "" : "2px solid red";
  $("#CheckEmail").html(message).css("color", color);
  $this.css("border", border);
});

$("form").on("focusout", function (e) {
  if (!$(e.relatedTarget).closest("form").length) return;
  const password = $("#password, #change_profile_password").val(), confirmPassword = $("#id_passwordconfirm, #change_profile_passwordconfirm").val(), email = $("#email, #change_profile_email").val();
  const username = $("#username").val();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (password === confirmPassword) $("#id_passwordconfirm, #password, #change_profile_password, #change_profile_passwordconfirm").css("border", "");
  if (emailRegex.test(email) && email !== "") $("#email, #change_profile_email").css("border", "");
  if (username) $("#username").css("border", "");
});


$("#delete-form-button").on("click", function () {
  // Find the closest form and remove 'required' attribute for oldpassword
  $(this).closest('.form-wrapper').find("#change_profile_oldpassword").prop("required", false);
});


$(document).ready(function () {
  $(".toggle-password").attr("role", "button");

  $(".toggle-password").on("click keydown", function (e) {
    if (e.type === "click" || (e.type === "keydown" && (e.key === "Enter" || e.key === " "))) {
      const toggleIcon = $(this);
      $("#password, #id_passwordconfirm, #change_profile_password, #change_profile_passwordconfirm, #delete_profile").each(function () { 
        const passwordField = $(this);
        const passwordFieldType = passwordField.attr("type");
        if (passwordFieldType == "password") {
          passwordField.attr("type", "text");
          toggleIcon.removeClass("fa-eye-slash").addClass("fa-eye");
          toggleIcon.attr("aria-label", "Hide password");
        } else {
          passwordField.attr("type", "password");
          toggleIcon.removeClass("fa-eye").addClass("fa-eye-slash");
          toggleIcon.attr("aria-label", "Show password");
        }
      });
    }
  });
});


$(document).ready(function () {
  $("#question-mark").attr("role", "button");
  $("#close-tooltip").attr("tabindex", "0");

  $("#question-mark, #exclamationIcon").on("click keydown", function (event) {
    if (event.type === "click" || (event.type === "keydown" && (event.key === "Enter" || event.key === " "))) {
      event.stopPropagation();
      const tooltip = $("#tooltip-content");
      tooltip.toggleClass("show-tooltip");
      if (tooltip.hasClass("show-tooltip")) $("#tooltip-content").focus();
    }
  });

  $(document).on("click", function () {
    $("#tooltip-content").removeClass("show-tooltip");
  });
});

//its working
window.onload = function () {
  if (focusPassword) {
    const passwordField = document.getElementById("password");
    if (passwordField) passwordField.focus();
  }
  if (focusUsername) {
    const usernameField = document.getElementById("username");
    if (usernameField) usernameField.focus();
  }
  //Scrolling to the top of the page when hash is pointing to an element
  var element = document.getElementById(location.hash.substring(1));
  if (element) {
    window.scrollTo(0, element.getBoundingClientRect().top + window.scrollY - 500);  
  }
};
    
