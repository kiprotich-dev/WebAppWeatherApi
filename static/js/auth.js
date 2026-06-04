const message = document.querySelector("#form-message");

function showMessage(text, type = "error") {
    message.textContent = text || "";
    message.classList.remove("error", "success");
    if (text) {
        message.classList.add(type);
    }
}

function storeSession(payload) {
    localStorage.setItem("weatherAccessToken", payload.tokens.access);
    localStorage.setItem("weatherRefreshToken", payload.tokens.refresh);
    localStorage.setItem("weatherUser", JSON.stringify(payload.user));
}

function formatErrors(payload) {
    if (payload.detail && !payload.errors) {
        return payload.detail;
    }
    if (!payload.errors) {
        return payload.detail || "Something went wrong.";
    }
    return Object.values(payload.errors).flat().join(" ");
}

async function submitAuth(endpoint, form) {
    const button = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const body = Object.fromEntries(formData.entries());

    button.disabled = true;
    showMessage("Loading...", "success");

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(formatErrors(payload));
        }
        storeSession(payload);
        window.location.href = "/";
    } catch (error) {
        showMessage(error.message);
    } finally {
        button.disabled = false;
    }
}

const loginForm = document.querySelector("#login-form");
if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        submitAuth("/api/auth/login", loginForm);
    });
}

const registerForm = document.querySelector("#register-form");
if (registerForm) {
    registerForm.addEventListener("submit", (event) => {
        event.preventDefault();
        submitAuth("/api/auth/register", registerForm);
    });
}
