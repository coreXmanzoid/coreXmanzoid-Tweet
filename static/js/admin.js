const supportRequests = [
    {
        id: "GH-1042",
        userId: "USR-1201",
        userName: "Ava Collins",
        category: "Login Issue",
        message: "I reset my password twice, but the login page keeps sending me back to the sign-in screen after authentication.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 08:25 AM",
        adminReply: ""
    },
    {
        id: "GH-1043",
        userId: "USR-1208",
        userName: "Noah Bennett",
        category: "Billing",
        message: "My premium plan renewed successfully, but the AI features are still locked on both desktop and mobile.",
        status: "Answered",
        timestamp: "Mar 24, 2026 - 09:10 AM",
        adminReply: "We refreshed premium access on the account and asked the user to sign out and back in."
    },
    {
        id: "GH-1044",
        userId: "USR-1215",
        userName: "Mia Reynolds",
        category: "Notifications",
        message: "Push notifications are delayed by around 20 minutes. I noticed it mostly on replies and new follower alerts.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 10:45 AM",
        adminReply: ""
    },
    {
        id: "GH-1045",
        userId: "USR-1224",
        userName: "Ethan Brooks",
        category: "Profile Update",
        message: "The profile image uploader finishes cropping, but the updated image does not show on my profile until I refresh several times.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 11:58 AM",
        adminReply: ""
    },
    {
        id: "GH-1046",
        userId: "USR-1230",
        userName: "Sophia Carter",
        category: "Account Recovery",
        message: "I no longer have access to my old email address and need help recovering my account without losing my saved settings.",
        status: "Answered",
        timestamp: "Mar 24, 2026 - 01:20 PM",
        adminReply: "We requested identity verification details and shared the recovery workflow."
    }
];

const userReports = [
    {
        id: "RP-7301",
        userId: "USR-2102",
        userName: "Liam Torres",
        text: "A user is repeatedly posting abusive comments under multiple threads and switching accounts after each block.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 08:48 AM"
    },
    {
        id: "RP-7302",
        userId: "USR-2134",
        userName: "Olivia Parker",
        text: "This account appears to be impersonating a creator and copying profile details, posts, and replies to mislead followers.",
        status: "Reviewed",
        timestamp: "Mar 24, 2026 - 09:32 AM"
    },
    {
        id: "RP-7303",
        userId: "USR-2160",
        userName: "James Foster",
        text: "Spam links are being dropped in comment threads with suspicious redirects that look unsafe for users.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 12:14 PM"
    },
    {
        id: "RP-7304",
        userId: "USR-2187",
        userName: "Charlotte Price",
        text: "A reported post includes hate speech that should be reviewed and removed before it spreads further.",
        status: "Pending",
        timestamp: "Mar 24, 2026 - 02:05 PM"
    }
];

const state = {
    activeSection: "dashboard",
    selectedSupportId: null,
    selectedReportId: null,
    supportQuery: "",
    supportStatus: "all",
    reportsQuery: "",
    reportsStatus: "all"
};

const pageMeta = {
    dashboard: { title: "Dashboard", kicker: "Admin Workspace" },
    support: { title: "Support Requests", kicker: "Support Desk" },
    reports: { title: "Reports", kicker: "Moderation Desk" }
};

const elements = {
    app: document.getElementById("adminApp"),
    pageTitle: document.getElementById("pageTitle"),
    pageKicker: document.getElementById("pageKicker"),
    supportTableBody: document.getElementById("supportTableBody"),
    reportsTableBody: document.getElementById("reportsTableBody"),
    supportEmptyState: document.getElementById("supportEmptyState"),
    reportsEmptyState: document.getElementById("reportsEmptyState"),
    supportSearchInput: document.getElementById("supportSearchInput"),
    supportStatusFilter: document.getElementById("supportStatusFilter"),
    reportsSearchInput: document.getElementById("reportsSearchInput"),
    reportsStatusFilter: document.getElementById("reportsStatusFilter"),
    supportPendingBadge: document.getElementById("supportPendingBadge"),
    reportsPendingBadge: document.getElementById("reportsPendingBadge"),
    supportTotalMetric: document.getElementById("supportTotalMetric"),
    pendingTotalMetric: document.getElementById("pendingTotalMetric"),
    answeredMetric: document.getElementById("answeredMetric"),
    reviewedMetric: document.getElementById("reviewedMetric"),
    dashboardSupportPending: document.getElementById("dashboardSupportPending"),
    dashboardReportsPending: document.getElementById("dashboardReportsPending"),
    supportSnapshotList: document.getElementById("supportSnapshotList"),
    reportSnapshotList: document.getElementById("reportSnapshotList"),
    currentDateLabel: document.getElementById("currentDateLabel"),
    adminReplyInput: document.getElementById("adminReplyInput"),
    sendReplyButton: document.getElementById("sendReplyButton"),
    markAnsweredButton: document.getElementById("markAnsweredButton"),
    markReviewedButton: document.getElementById("markReviewedButton"),
    modalSupportId: document.getElementById("modalSupportId"),
    modalSupportUser: document.getElementById("modalSupportUser"),
    modalSupportCategory: document.getElementById("modalSupportCategory"),
    modalSupportStatus: document.getElementById("modalSupportStatus"),
    modalSupportTimestamp: document.getElementById("modalSupportTimestamp"),
    modalSupportMessage: document.getElementById("modalSupportMessage"),
    modalReportId: document.getElementById("modalReportId"),
    modalReportUser: document.getElementById("modalReportUser"),
    modalReportStatus: document.getElementById("modalReportStatus"),
    modalReportTimestamp: document.getElementById("modalReportTimestamp"),
    modalReportMessage: document.getElementById("modalReportMessage"),
    sidebarOpenButton: document.getElementById("sidebarOpenButton"),
    sidebarCloseButton: document.getElementById("sidebarCloseButton"),
    sidebarBackdrop: document.getElementById("sidebarBackdrop")
};

const supportModal = new bootstrap.Modal(document.getElementById("supportDetailsModal"));
const reportModal = new bootstrap.Modal(document.getElementById("reportDetailsModal"));

function formatCurrentDate() {
    const now = new Date();
    elements.currentDateLabel.textContent = now.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric"
    });
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getStatusClass(status) {
    const normalized = status.toLowerCase();
    if (normalized === "answered") {
        return "answered";
    }
    if (normalized === "reviewed") {
        return "reviewed";
    }
    return "pending";
}

function getFilteredSupportRequests() {
    const query = state.supportQuery.trim().toLowerCase();
    return supportRequests.filter((item) => {
        const matchesStatus = state.supportStatus === "all" || item.status === state.supportStatus;
        const matchesQuery = !query || [item.id, item.userId, item.userName, item.category, item.message]
            .some((field) => field.toLowerCase().includes(query));
        return matchesStatus && matchesQuery;
    });
}

function getFilteredReports() {
    const query = state.reportsQuery.trim().toLowerCase();
    return userReports.filter((item) => {
        const matchesStatus = state.reportsStatus === "all" || item.status === state.reportsStatus;
        const matchesQuery = !query || [item.id, item.userId, item.userName, item.text]
            .some((field) => field.toLowerCase().includes(query));
        return matchesStatus && matchesQuery;
    });
}

function renderSupportTable() {
    const filtered = getFilteredSupportRequests();
    elements.supportTableBody.innerHTML = filtered.map((item) => `
        <tr>
            <td data-label="Request ID"><strong>${escapeHtml(item.id)}</strong><div class="table-meta">${escapeHtml(item.timestamp)}</div></td>
            <td data-label="User">
                <div class="user-block">
                    <span class="user-name">${escapeHtml(item.userName)}</span>
                    <span class="user-id">${escapeHtml(item.userId)}</span>
                </div>
            </td>
            <td data-label="Category">${escapeHtml(item.category)}</td>
            <td data-label="Message"><div class="message-preview">${escapeHtml(item.message)}</div></td>
            <td data-label="Status"><span class="status-pill ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span></td>
            <td data-label="Action" class="text-end row-action-cell">
                <button class="row-action-button" type="button" data-support-id="${escapeHtml(item.id)}">View Details</button>
            </td>
        </tr>
    `).join("");

    elements.supportEmptyState.classList.toggle("d-none", filtered.length > 0);
}

function renderReportsTable() {
    const filtered = getFilteredReports();
    elements.reportsTableBody.innerHTML = filtered.map((item) => `
        <tr>
            <td data-label="Report ID"><strong>${escapeHtml(item.id)}</strong><div class="table-meta">${escapeHtml(item.timestamp)}</div></td>
            <td data-label="User">
                <div class="user-block">
                    <span class="user-name">${escapeHtml(item.userName)}</span>
                    <span class="user-id">${escapeHtml(item.userId)}</span>
                </div>
            </td>
            <td data-label="Report Text"><div class="message-preview">${escapeHtml(item.text)}</div></td>
            <td data-label="Status"><span class="status-pill ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span></td>
            <td data-label="Action" class="text-end row-action-cell">
                <button class="row-action-button" type="button" data-report-id="${escapeHtml(item.id)}">View Details</button>
            </td>
        </tr>
    `).join("");

    elements.reportsEmptyState.classList.toggle("d-none", filtered.length > 0);
}

function renderDashboardSnapshots() {
    const supportSnapshot = supportRequests.slice(0, 3);
    const reportSnapshot = userReports.slice(0, 3);

    elements.supportSnapshotList.innerHTML = supportSnapshot.map((item) => `
        <article class="snapshot-item">
            <div>
                <h4>${escapeHtml(item.userName)} <span class="snapshot-meta">- ${escapeHtml(item.category)}</span></h4>
                <p>${escapeHtml(item.message)}</p>
            </div>
            <span class="status-pill ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span>
        </article>
    `).join("");

    elements.reportSnapshotList.innerHTML = reportSnapshot.map((item) => `
        <article class="snapshot-item">
            <div>
                <h4>${escapeHtml(item.userName)}</h4>
                <p>${escapeHtml(item.text)}</p>
            </div>
            <span class="status-pill ${getStatusClass(item.status)}">${escapeHtml(item.status)}</span>
        </article>
    `).join("");
}

function updateMetrics() {
    const supportPending = supportRequests.filter((item) => item.status === "Pending").length;
    const reportsPending = userReports.filter((item) => item.status === "Pending").length;
    const answeredCount = supportRequests.filter((item) => item.status === "Answered").length;
    const reviewedCount = userReports.filter((item) => item.status === "Reviewed").length;

    elements.supportPendingBadge.textContent = supportPending;
    elements.reportsPendingBadge.textContent = reportsPending;
    elements.supportTotalMetric.textContent = supportRequests.length;
    elements.pendingTotalMetric.textContent = supportPending + reportsPending;
    elements.answeredMetric.textContent = answeredCount;
    elements.reviewedMetric.textContent = reviewedCount;
    elements.dashboardSupportPending.textContent = supportPending;
    elements.dashboardReportsPending.textContent = reportsPending;
}

function switchSection(sectionName) {
    state.activeSection = sectionName;
    document.querySelectorAll(".nav-item").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.section === sectionName);
    });
    document.querySelectorAll("[data-section-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.sectionPanel === sectionName);
    });
    elements.pageTitle.textContent = pageMeta[sectionName].title;
    elements.pageKicker.textContent = pageMeta[sectionName].kicker;
    closeSidebar();
}

function openSupportModal(requestId) {
    const request = supportRequests.find((item) => item.id === requestId);
    if (!request) {
        return;
    }
    state.selectedSupportId = requestId;
    elements.modalSupportId.textContent = request.id;
    elements.modalSupportUser.textContent = `${request.userName} (${request.userId})`;
    elements.modalSupportCategory.textContent = request.category;
    elements.modalSupportStatus.textContent = request.status;
    elements.modalSupportTimestamp.textContent = request.timestamp;
    elements.modalSupportMessage.textContent = request.message;
    elements.adminReplyInput.value = request.adminReply || "";
    supportModal.show();
}

function openReportModal(reportId) {
    const report = userReports.find((item) => item.id === reportId);
    if (!report) {
        return;
    }
    state.selectedReportId = reportId;
    elements.modalReportId.textContent = report.id;
    elements.modalReportUser.textContent = `${report.userName} (${report.userId})`;
    elements.modalReportStatus.textContent = report.status;
    elements.modalReportTimestamp.textContent = report.timestamp;
    elements.modalReportMessage.textContent = report.text;
    reportModal.show();
}

function showToast(message) {
    const toastHostId = "toastShell";
    let toastShell = document.getElementById(toastHostId);
    if (!toastShell) {
        toastShell = document.createElement("div");
        toastShell.id = toastHostId;
        toastShell.className = "toast-shell";
        document.body.appendChild(toastShell);
    }

    const toastElement = document.createElement("div");
    toastElement.className = "toast custom-toast align-items-center border-0";
    toastElement.setAttribute("role", "alert");
    toastElement.setAttribute("aria-live", "assertive");
    toastElement.setAttribute("aria-atomic", "true");
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-semibold">${escapeHtml(message)}</div>
            <button type="button" class="btn-close me-3 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastShell.appendChild(toastElement);
    const toast = new bootstrap.Toast(toastElement, { delay: 2200 });
    toast.show();
    toastElement.addEventListener("hidden.bs.toast", () => toastElement.remove());
}

function saveAdminReply() {
    const request = supportRequests.find((item) => item.id === state.selectedSupportId);
    if (!request) {
        return;
    }
    const reply = elements.adminReplyInput.value.trim();
    if (!reply) {
        showToast("Add a reply before sending.");
        return;
    }
    request.adminReply = reply;
    showToast(`Reply saved for ${request.id}.`);
}

function markSupportAnswered() {
    const request = supportRequests.find((item) => item.id === state.selectedSupportId);
    if (!request) {
        return;
    }
    request.adminReply = elements.adminReplyInput.value.trim();
    request.status = "Answered";
    elements.modalSupportStatus.textContent = request.status;
    renderAll();
    showToast(`${request.id} marked as answered.`);
}

function markReportReviewed() {
    const report = userReports.find((item) => item.id === state.selectedReportId);
    if (!report) {
        return;
    }
    report.status = "Reviewed";
    elements.modalReportStatus.textContent = report.status;
    renderAll();
    showToast(`${report.id} marked as reviewed.`);
}

function openSidebar() {
    elements.app.classList.add("sidebar-open");
}

function closeSidebar() {
    elements.app.classList.remove("sidebar-open");
}

function renderAll() {
    renderSupportTable();
    renderReportsTable();
    renderDashboardSnapshots();
    updateMetrics();
}

function bindEvents() {
    document.querySelectorAll(".nav-item").forEach((button) => {
        button.addEventListener("click", () => switchSection(button.dataset.section));
    });

    document.querySelectorAll("[data-section-jump]").forEach((button) => {
        button.addEventListener("click", () => switchSection(button.dataset.sectionJump));
    });

    elements.supportSearchInput.addEventListener("input", (event) => {
        state.supportQuery = event.target.value;
        renderSupportTable();
    });

    elements.supportStatusFilter.addEventListener("change", (event) => {
        state.supportStatus = event.target.value;
        renderSupportTable();
    });

    elements.reportsSearchInput.addEventListener("input", (event) => {
        state.reportsQuery = event.target.value;
        renderReportsTable();
    });

    elements.reportsStatusFilter.addEventListener("change", (event) => {
        state.reportsStatus = event.target.value;
        renderReportsTable();
    });

    elements.supportTableBody.addEventListener("click", (event) => {
        const button = event.target.closest("[data-support-id]");
        if (button) {
            openSupportModal(button.dataset.supportId);
        }
    });

    elements.reportsTableBody.addEventListener("click", (event) => {
        const button = event.target.closest("[data-report-id]");
        if (button) {
            openReportModal(button.dataset.reportId);
        }
    });

    elements.sendReplyButton.addEventListener("click", saveAdminReply);
    elements.markAnsweredButton.addEventListener("click", markSupportAnswered);
    elements.markReviewedButton.addEventListener("click", markReportReviewed);
    elements.sidebarOpenButton.addEventListener("click", openSidebar);
    elements.sidebarCloseButton.addEventListener("click", closeSidebar);
    elements.sidebarBackdrop.addEventListener("click", closeSidebar);
}

function init() {
    formatCurrentDate();
    bindEvents();
    renderAll();
    switchSection("dashboard");
}

init();
