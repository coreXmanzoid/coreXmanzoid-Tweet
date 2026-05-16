const firebaseRuntimeConfig = window.firebaseRuntimeConfig || {};
const firebaseEnabled = Boolean(firebaseRuntimeConfig.firebaseEnabled);
const vapidKey = firebaseRuntimeConfig.vapidKey || "";
const firebaseMessagingSwPath = "/firebase-messaging-sw.js";
const firebaseConfig = firebaseRuntimeConfig.firebaseConfig || {};

let messaging = null;
let firebaseMessagingRegistrationPromise = null;
let firebaseMessagingReadyPromise = null;

function getNotificationPayload(payload) {
    const notification = payload && payload.notification ? payload.notification : {};
    const data = payload && payload.data ? payload.data : {};

    return {
        title: notification.title || data.title || "ChatFlick",
        body: notification.body || data.body || "",
        icon: notification.icon || data.icon || "/static/assets/logo.png",
        data: data
    };
}

function getFirebaseMessagingRegistration() {
    if (!firebaseMessagingRegistrationPromise) {
        firebaseMessagingRegistrationPromise = navigator.serviceWorker.register(firebaseMessagingSwPath, {
            scope: "/"
        });
    }

    return firebaseMessagingRegistrationPromise;
}

async function isFirebaseMessagingSupported() {
    if (!window.firebase || !window.firebase.messaging) {
        return false;
    }

    if (typeof firebase.messaging.isSupported !== "function") {
        return true;
    }

    return await firebase.messaging.isSupported();
}

async function initializeFirebaseMessaging() {
    if (firebaseMessagingReadyPromise) {
        return firebaseMessagingReadyPromise;
    }

    firebaseMessagingReadyPromise = (async function () {
        if (!firebaseEnabled) {
            return null;
        }

        if (!(await isFirebaseMessagingSupported())) {
            console.warn("Firebase Messaging is not supported in this browser.");
            return null;
        }

        try {
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
            }

            messaging = firebase.messaging();
            messaging.onMessage(showForegroundNotification);
            return messaging;
        } catch (error) {
            console.error("Firebase Messaging failed to initialize:", error);
            messaging = null;
            return null;
        }
    })();

    return firebaseMessagingReadyPromise;
}

async function showForegroundNotification(payload) {
    if (!("Notification" in window) || Notification.permission !== "granted") {
        return;
    }

    const notification = getNotificationPayload(payload);

    try {
        if ("serviceWorker" in navigator) {
            const registration = await getFirebaseMessagingRegistration();
            await registration.showNotification(notification.title, {
                body: notification.body,
                icon: notification.icon,
                data: notification.data
            });
            return;
        }

        if (typeof Notification === "function") {
            new Notification(notification.title, {
                body: notification.body,
                icon: notification.icon,
                data: notification.data
            });
        }
    } catch (error) {
        console.error("Unable to show foreground notification:", error);
    }
}

async function enableNotifications(allowPermissionPrompt = true) {
    try {
        if (!firebaseEnabled) {
            if (allowPermissionPrompt) alert("Push notifications are not available right now.");
            return;
        }

        if (!("serviceWorker" in navigator)) {
            if (allowPermissionPrompt) alert("Service workers are not supported in this browser.");
            return;
        }

        if (!window.isSecureContext) {
            if (allowPermissionPrompt) alert("Push notifications require HTTPS.");
            return;
        }

        if (!("Notification" in window)) {
            if (allowPermissionPrompt) alert("Notifications are not supported in this browser.");
            return;
        }

        if (!vapidKey) {
            if (allowPermissionPrompt) alert("FCM_VAPID_KEY is not configured on the server.");
            return;
        }

        const activeMessaging = await initializeFirebaseMessaging();
        if (!activeMessaging) {
            if (allowPermissionPrompt) alert("Firebase Messaging is not available in this browser.");
            return;
        }

        const registration = await getFirebaseMessagingRegistration();
        let permission = Notification.permission;
        if (permission !== "granted" && allowPermissionPrompt) {
            permission = await Notification.requestPermission();
        }

        if (permission !== "granted") {
            if (allowPermissionPrompt) alert("Permission denied");
            return;
        }

        const token = await activeMessaging.getToken({
            vapidKey: vapidKey,
            serviceWorkerRegistration: registration
        });

        if (!token) {
            if (allowPermissionPrompt) alert("Could not get FCM token.");
            return;
        }

        const response = await fetch("/save-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: token })
        });

        if (!response.ok) {
            if (allowPermissionPrompt) alert("Failed to save notification token.");
            return;
        }

        const result = await response.json();
        if (result.status !== "saved") {
            if (allowPermissionPrompt) alert("Failed to save notification token.");
            return;
        }

        if (allowPermissionPrompt) {
            alert("Notifications enabled");
        }

        $("#notifications-permission").remove();
        $(".notifications").show();
    } catch (error) {
        console.error("Push notification setup failed:", error);
        if (allowPermissionPrompt) alert("Unable to enable push notifications right now.");
    }
}

function requestNotificationPermission() {
    return enableNotifications(true);
}

document.addEventListener("click", function (event) {
    if (event.target && event.target.closest(".notifications-allow")) {
        event.preventDefault();
        enableNotifications(true);
    }
});

initializeFirebaseMessaging().then(function () {
    if ("Notification" in window && Notification.permission === "granted") {
        enableNotifications(false);
    }
});

window.enableNotifications = enableNotifications;
window.requestNotificationPermission = requestNotificationPermission;
