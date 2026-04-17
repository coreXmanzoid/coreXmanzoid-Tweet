let supportRequests = [];
let userReports = [];
let managedUsers = [];

const state = {
    activeSection: "dashboard",
    selectedSupportId: null,
    selectedReportId: null,
    selectedUserId: null,
    sidebarCollapsed: false,
    supportQuery: "",
    supportStatus: "all",
    reportsQuery: "",
    reportsStatus: "all",
    usersQuery: "",
    usersFilter: "all"
};

const pageMeta = {
    dashboard: { title: "Dashboard", kicker: "Admin Workspace" },
    support: { title: "Support Requests", kicker: "Support Desk" },
    reports: { title: "Reports", kicker: "Moderation Desk" },
    users: { title: "Users", kicker: "Account Control" }
};

const el = {
    app: document.getElementById("adminApp"),
    pageTitle: document.getElementById("pageTitle"),
    pageKicker: document.getElementById("pageKicker"),
    supportTableBody: document.getElementById("supportTableBody"),
    reportsTableBody: document.getElementById("reportsTableBody"),
    usersTableBody: document.getElementById("usersTableBody"),
    usersOverviewGrid: document.getElementById("usersOverviewGrid"),
    supportEmptyState: document.getElementById("supportEmptyState"),
    reportsEmptyState: document.getElementById("reportsEmptyState"),
    usersEmptyState: document.getElementById("usersEmptyState"),
    supportSearchInput: document.getElementById("supportSearchInput"),
    supportStatusFilter: document.getElementById("supportStatusFilter"),
    reportsSearchInput: document.getElementById("reportsSearchInput"),
    reportsStatusFilter: document.getElementById("reportsStatusFilter"),
    usersSearchInput: document.getElementById("usersSearchInput"),
    usersFilterTabs: document.getElementById("usersFilterTabs"),
    supportPendingBadge: document.getElementById("supportPendingBadge"),
    reportsPendingBadge: document.getElementById("reportsPendingBadge"),
    usersBlockedBadge: document.getElementById("usersBlockedBadge"),
    selectedUserName: document.getElementById("selectedUserName"),
    selectedUserMeta: document.getElementById("selectedUserMeta"),
    selectedUserInitials: document.getElementById("selectedUserInitials"),
    selectedUserEmail: document.getElementById("selectedUserEmail"),
    selectedUserBadges: document.getElementById("selectedUserBadges"),
    selectedUserNote: document.getElementById("selectedUserNote"),
    selectedUserProfileButton: document.getElementById("selectedUserProfileButton"),
    panelVerifyButton: document.getElementById("panelVerifyButton"),
    panelProTitle: document.getElementById("panelProTitle"),
    panelProDescription: document.getElementById("panelProDescription"),
    panelProPrimaryButton: document.getElementById("panelProPrimaryButton"),
    panelProSecondaryButton: document.getElementById("panelProSecondaryButton"),
    panelBlockTitle: document.getElementById("panelBlockTitle"),
    panelBlockDescription: document.getElementById("panelBlockDescription"),
    panelWarningButton: document.getElementById("panelWarningButton"),
    panelBlockButton: document.getElementById("panelBlockButton"),
    supportTotalMetric: document.getElementById("supportTotalMetric"),
    usersTotalMetric: document.getElementById("usersTotalMetric"),
    pendingProMetric: document.getElementById("pendingProMetric"),
    blockedUsersMetric: document.getElementById("blockedUsersMetric"),
    pendingTotalMetric: document.getElementById("pendingTotalMetric"),
    answeredMetric: document.getElementById("answeredMetric"),
    reviewedMetric: document.getElementById("reviewedMetric"),
    verifiedUsersMetric: document.getElementById("verifiedUsersMetric"),
    dashboardSupportPending: document.getElementById("dashboardSupportPending"),
    dashboardReportsPending: document.getElementById("dashboardReportsPending"),
    dashboardPendingPro: document.getElementById("dashboardPendingPro"),
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
    sidebarCollapseButton: document.getElementById("sidebarCollapseButton"),
    sidebarOpenButton: document.getElementById("sidebarOpenButton"),
    sidebarCloseButton: document.getElementById("sidebarCloseButton"),
    sidebarBackdrop: document.getElementById("sidebarBackdrop")
};

const supportModal = new bootstrap.Modal(document.getElementById("supportDetailsModal"));
const reportModal = new bootstrap.Modal(document.getElementById("reportDetailsModal"));

const esc = (v) => String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const statusClass = (status) => {
    const s = String(status).toLowerCase();
    if (s === "answered") return "answered";
    if (s === "reviewed") return "reviewed";
    if (s === "blocked") return "blocked";
    if (s === "verified") return "verified";
    return "pending";
};

function currentDate() {
    el.currentDateLabel.textContent = new Date().toLocaleDateString("en-US", {
        month: "long", day: "numeric", year: "numeric"
    });
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.status === "error") {
        throw new Error(payload.message || "Request failed");
    }
    return payload;
}

async function loadDashboard() {
    const payload = await api("/admin/api/dashboard");
    supportRequests = payload.data?.supportRequests || [];
    userReports = payload.data?.userReports || [];
    managedUsers = payload.data?.managedUsers || [];
    if (!managedUsers.some((u) => u.id === state.selectedUserId)) {
        state.selectedUserId = managedUsers[0]?.id || null;
    }
    renderAll();
}

function selectedUser() {
    return managedUsers.find((u) => u.id === state.selectedUserId) || managedUsers[0] || null;
}

function initials(name) {
    return String(name || "").split(" ").filter(Boolean).slice(0, 2).map((v) => v[0].toUpperCase()).join("");
}

function filterSupport() {
    const q = state.supportQuery.trim().toLowerCase();
    return supportRequests.filter((item) => {
        const okStatus = state.supportStatus === "all" || item.status === state.supportStatus;
        const okQuery = !q || [item.id, item.userId, item.userName, item.category, item.message]
            .some((field) => String(field).toLowerCase().includes(q));
        return okStatus && okQuery;
    });
}

function filterReports() {
    const q = state.reportsQuery.trim().toLowerCase();
    return userReports.filter((item) => {
        const okStatus = state.reportsStatus === "all" || item.status === state.reportsStatus;
        const okQuery = !q || [item.id, item.userId, item.userName, item.text]
            .some((field) => String(field).toLowerCase().includes(q));
        return okStatus && okQuery;
    });
}

function filterUsers() {
    const q = state.usersQuery.trim().toLowerCase();
    return managedUsers.filter((item) => {
        const okFilter =
            state.usersFilter === "all" ||
            (state.usersFilter === "verified" && item.verified) ||
            (state.usersFilter === "pending-pro" && item.pendingPro) ||
            (state.usersFilter === "pro" && item.pro) ||
            (state.usersFilter === "blocked" && item.status === "Blocked");
        const okQuery = !q || [item.id, item.name, item.email]
            .some((field) => String(field).toLowerCase().includes(q));
        return okFilter && okQuery;
    });
}

function renderSupportTable() {
    const rows = filterSupport();
    el.supportTableBody.innerHTML = rows.map((item) => `
        <tr>
            <td data-label="Request ID"><strong>${esc(item.id)}</strong><div class="table-meta">${esc(item.timestamp)}</div></td>
            <td data-label="User"><div class="user-block"><span class="user-name">${esc(item.userName)}</span><span class="user-id">${esc(item.userId)}</span></div></td>
            <td data-label="Category">${esc(item.category)}</td>
            <td data-label="Message"><div class="message-preview">${esc(item.message)}</div></td>
            <td data-label="Status"><span class="status-pill ${statusClass(item.status)}">${esc(item.status)}</span></td>
            <td data-label="Action" class="text-end row-action-cell"><button class="row-action-button" type="button" data-support-id="${esc(item.id)}">View Details</button></td>
        </tr>
    `).join("");
    el.supportEmptyState.classList.toggle("d-none", rows.length > 0);
}

function renderReportsTable() {
    const rows = filterReports();
    el.reportsTableBody.innerHTML = rows.map((item) => `
        <tr>
            <td data-label="Report ID"><strong>${esc(item.id)}</strong><div class="table-meta">${esc(item.timestamp)}</div></td>
            <td data-label="User"><div class="user-block"><span class="user-name">${esc(item.userName)}</span><span class="user-id">${esc(item.userId)}</span></div></td>
            <td data-label="Report Text"><div class="message-preview">${esc(item.text)}</div></td>
            <td data-label="Status"><span class="status-pill ${statusClass(item.status)}">${esc(item.status)}</span></td>
            <td data-label="Action" class="text-end row-action-cell"><button class="row-action-button" type="button" data-report-id="${esc(item.id)}">View Details</button></td>
        </tr>
    `).join("");
    el.reportsEmptyState.classList.toggle("d-none", rows.length > 0);
}

function renderUsersOverview() {
    const verified = managedUsers.filter((v) => v.verified).length;
    const pending = managedUsers.filter((v) => v.pendingPro).length;
    const pro = managedUsers.filter((v) => v.pro).length;
    const blocked = managedUsers.filter((v) => v.status === "Blocked").length;
    el.usersOverviewGrid.innerHTML = `
        <article class="users-overview-card"><span class="mini-label">Verified Accounts</span><strong>${verified}</strong><p>Accounts ready for advanced access and trusted actions.</p></article>
        <article class="users-overview-card"><span class="mini-label">Pending Pro</span><strong>${pending}</strong><p>Premium requests waiting for admin approval or rejection.</p></article>
        <article class="users-overview-card"><span class="mini-label">Pro Members</span><strong>${pro}</strong><p>Users currently holding premium status inside the dashboard.</p></article>
        <article class="users-overview-card"><span class="mini-label">Blocked Users</span><strong>${blocked}</strong><p>Restricted accounts that have management actions disabled.</p></article>
    `;
}

function renderUsersTable() {
    const rows = filterUsers();
    if (rows.length && !rows.some((v) => v.id === state.selectedUserId)) {
        state.selectedUserId = rows[0].id;
    }
    el.usersTableBody.innerHTML = rows.map((item) => {
        const blocked = item.status === "Blocked";
        const selected = item.id === state.selectedUserId;
        const proClass = item.pendingPro ? "pending-pro" : item.pro ? "pro" : "inactive";
        const proIcon = item.pendingPro ? "bi-hourglass-split" : item.pro ? "bi-stars" : "bi-dash-circle";
        const proLabel = item.pendingPro ? "Pending Pro" : item.pro ? "Pro" : "Standard";
        return `
            <tr class="user-row ${blocked ? "is-blocked" : ""} ${selected ? "is-selected" : ""}" data-user-select="${esc(item.id)}">
                <td data-label="User"><div class="table-user-identity"><div class="table-user-avatar">${esc(initials(item.name))}</div><div class="user-block"><span class="user-name">${esc(item.name)}</span><span class="user-id">${esc(item.id)}</span></div></div></td>
                <td data-label="Email"><span class="user-email">${esc(item.email)}</span></td>
                <td data-label="Verification"><span class="status-pill ${item.verified ? "verified" : "inactive"}"><i class="bi ${item.verified ? "bi-check-circle-fill" : "bi-dash-circle"}"></i>${item.verified ? "Verified" : "Unverified"}</span></td>
                <td data-label="Pro Plan"><span class="status-pill ${proClass}"><i class="bi ${proIcon}"></i>${proLabel}</span></td>
                <td data-label="Account"><span class="status-pill ${blocked ? "blocked" : item.status === "Deactivated" ? "inactive" : "verified"}"><i class="bi ${blocked ? "bi-slash-circle-fill" : item.status === "Deactivated" ? "bi-pause-circle" : "bi-shield-check"}"></i>${esc(item.status)}</span></td>
                <td data-label="Manage" class="text-end row-action-cell"><button class="row-action-button" type="button" data-user-select="${esc(item.id)}">${selected ? "Selected" : "Open Controls"}</button></td>
            </tr>
        `;
    }).join("");
    el.usersEmptyState.classList.toggle("d-none", rows.length > 0);
    document.querySelectorAll("[data-user-filter]").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.userFilter === state.usersFilter);
    });
}

function renderUserPanel() {
    const user = selectedUser();
    if (!user) {
        el.selectedUserName.textContent = "No users found";
        el.selectedUserMeta.textContent = "-";
        el.selectedUserInitials.textContent = "--";
        el.selectedUserEmail.textContent = "-";
        el.selectedUserBadges.innerHTML = "";
        el.selectedUserNote.textContent = "No user is available for admin review right now.";
        [el.panelVerifyButton, el.panelProPrimaryButton, el.panelProSecondaryButton, el.panelWarningButton, el.panelBlockButton].forEach((button) => {
            button.disabled = true;
        });
        return;
    }

    const blocked = user.status === "Blocked";
    const warningLabel = `${user.warnings} warning${user.warnings === 1 ? "" : "s"}`;
    el.selectedUserName.textContent = user.name;
    el.selectedUserMeta.textContent = `${user.id} - ${blocked ? "Restricted account" : "Member account"}`;
    el.selectedUserInitials.textContent = initials(user.name);
    el.selectedUserEmail.textContent = user.email;
    el.selectedUserBadges.innerHTML = [
        `<span class="status-pill ${user.verified ? "verified" : "inactive"}"><i class="bi ${user.verified ? "bi-check-circle-fill" : "bi-dash-circle"}"></i>${user.verified ? "Verified" : "Unverified"}</span>`,
        `<span class="status-pill ${user.pendingPro ? "pending-pro" : user.pro ? "pro" : "inactive"}"><i class="bi ${user.pendingPro ? "bi-hourglass-split" : user.pro ? "bi-stars" : "bi-dash-circle"}"></i>${user.pendingPro ? "Pending Pro" : user.pro ? "Pro" : "Standard"}</span>`,
        `<span class="status-pill ${blocked ? "blocked" : "verified"}"><i class="bi ${blocked ? "bi-slash-circle-fill" : "bi-shield-check"}"></i>${esc(user.status)}</span>`,
        `<span class="status-pill ${user.warnings > 0 ? "pending" : "inactive"}"><i class="bi bi-exclamation-triangle"></i>${esc(warningLabel)}</span>`
    ].join("");
    el.selectedUserNote.textContent = blocked
        ? "This account is blocked. Unblock it to restore the previous saved account state."
        : user.pendingPro
            ? "This account has a pending premium request. Approve it to grant Pro access or reject it to keep the verified plan."
            : user.pro
                ? "This user already has active Pro access. Moderation controls remain available."
                : user.verified
                    ? `This account is verified and ready for premium review. Current moderation history: ${warningLabel}.`
                    : `Verify this user first before approving any premium workflow. Current moderation history: ${warningLabel}.`;

    el.panelVerifyButton.disabled = blocked || user.verified;
    el.panelProTitle.textContent = user.pendingPro ? "Review premium request" : "Premium request status";
    el.panelProDescription.textContent = user.pendingPro
        ? "This user is waiting for a premium decision. Approve or reject the request below."
        : user.pro
            ? "This account already has active Pro access."
            : user.verified
                ? "No pending request is open right now."
                : "This account must be verified before any Pro request can be approved.";
    el.panelProPrimaryButton.textContent = user.pendingPro ? "Approve Pro" : user.pro ? "Pro Active" : "No Pending Request";
    el.panelProPrimaryButton.disabled = blocked || !user.pendingPro;
    el.panelProSecondaryButton.textContent = user.pendingPro ? "Reject Pro" : "Nothing to Reject";
    el.panelProSecondaryButton.disabled = blocked || !user.pendingPro;
    el.panelBlockTitle.textContent = blocked ? "Restore this account" : "Restrict this account";
    el.panelBlockDescription.textContent = blocked
        ? "Remove the restriction and restore the user to the last saved account state."
        : "Send a warning first or block the user and disable the remaining actions.";
    el.panelWarningButton.disabled = blocked;
    el.panelBlockButton.disabled = false;
    el.panelBlockButton.textContent = blocked ? "Unblock User" : "Block User";
    el.panelBlockButton.classList.toggle("action-unblock", blocked);
    el.panelBlockButton.classList.toggle("action-block", !blocked);
}

function updateMetrics() {
    const supportPending = supportRequests.filter((v) => v.status === "Pending").length;
    const reportPending = userReports.filter((v) => v.status === "Pending").length;
    const blocked = managedUsers.filter((v) => v.status === "Blocked").length;
    const verified = managedUsers.filter((v) => v.verified).length;
    el.supportPendingBadge.textContent = supportPending;
    el.reportsPendingBadge.textContent = reportPending;
    el.usersBlockedBadge.textContent = blocked;
    el.supportTotalMetric.textContent = supportRequests.length;
    el.usersTotalMetric.textContent = managedUsers.length;
    el.pendingProMetric.textContent = managedUsers.filter((v) => v.pendingPro).length;
    el.blockedUsersMetric.textContent = blocked;
    el.pendingTotalMetric.textContent = supportPending + reportPending;
    el.answeredMetric.textContent = supportRequests.filter((v) => v.status === "Answered").length;
    el.reviewedMetric.textContent = userReports.filter((v) => v.status === "Reviewed").length;
    el.verifiedUsersMetric.textContent = verified;
    el.dashboardSupportPending.textContent = supportPending;
    el.dashboardReportsPending.textContent = reportPending;
    el.dashboardPendingPro.textContent = managedUsers.filter((v) => v.pendingPro).length;
}

function renderAll() {
    renderSupportTable();
    renderReportsTable();
    renderUsersOverview();
    renderUsersTable();
    renderUserPanel();
    updateMetrics();
}

function switchSection(name) {
    state.activeSection = name;
    document.querySelectorAll(".nav-item").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.section === name);
    });
    document.querySelectorAll("[data-section-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.sectionPanel === name);
    });
    el.pageTitle.textContent = pageMeta[name].title;
    el.pageKicker.textContent = pageMeta[name].kicker;
    closeSidebar();
}

function showToast(message) {
    let shell = document.getElementById("toastShell");
    if (!shell) {
        shell = document.createElement("div");
        shell.id = "toastShell";
        shell.className = "toast-shell";
        document.body.appendChild(shell);
    }
    const toastEl = document.createElement("div");
    toastEl.className = "toast custom-toast align-items-center border-0";
    toastEl.innerHTML = `<div class="d-flex"><div class="toast-body fw-semibold">${esc(message)}</div><button type="button" class="btn-close me-3 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
    shell.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 2200 });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

function openSupportModal(id) {
    const item = supportRequests.find((v) => v.id === id);
    if (!item) return;
    state.selectedSupportId = id;
    el.modalSupportId.textContent = item.id;
    el.modalSupportUser.textContent = `${item.userName} (${item.userId})`;
    el.modalSupportCategory.textContent = item.category;
    el.modalSupportStatus.textContent = item.status;
    el.modalSupportTimestamp.textContent = item.timestamp;
    el.modalSupportMessage.textContent = item.message;
    el.adminReplyInput.value = item.adminReply || "";
    supportModal.show();
}

function openReportModal(id) {
    const item = userReports.find((v) => v.id === id);
    if (!item) return;
    state.selectedReportId = id;
    el.modalReportId.textContent = item.id;
    el.modalReportUser.textContent = `${item.userName} (${item.userId})`;
    el.modalReportStatus.textContent = item.status;
    el.modalReportTimestamp.textContent = item.timestamp;
    el.modalReportMessage.textContent = item.text;
    reportModal.show();
}

async function saveReply() {
    const item = supportRequests.find((v) => v.id === state.selectedSupportId);
    const reply = el.adminReplyInput.value.trim();
    if (!item) return;
    if (!reply) {
        showToast("Add a reply before sending.");
        return;
    }
    await api(`/admin/api/support/${item.dbId}/reply`, { method: "POST", body: JSON.stringify({ reply }) });
    await loadDashboard();
    openSupportModal(item.id);
    showToast(`Reply saved for ${item.id}.`);
}

async function markAnswered() {
    const item = supportRequests.find((v) => v.id === state.selectedSupportId);
    if (!item) return;
    await api(`/admin/api/support/${item.dbId}/answer`, {
        method: "POST",
        body: JSON.stringify({ reply: el.adminReplyInput.value.trim() })
    });
    await loadDashboard();
    openSupportModal(item.id);
    showToast(`${item.id} marked as answered.`);
}

async function markReviewed() {
    const item = userReports.find((v) => v.id === state.selectedReportId);
    if (!item) return;
    await api(`/admin/api/reports/${item.dbId}/review`, { method: "POST" });
    await loadDashboard();
    openReportModal(item.id);
    showToast(`${item.id} marked as reviewed.`);
}

async function userAction(action) {
    const user = selectedUser();
    if (!user) return;
    const map = {
        verify: "verify",
        approvePro: "approve-pro",
        rejectPro: "reject-pro",
        warning: "warning",
        block: "block",
        unblock: "unblock"
    };
    await api(`/admin/api/users/${user.dbId}/${map[action]}`, { method: "POST" });
    await loadDashboard();
    const latest = selectedUser() || user;
    const messages = {
        verify: `${latest.name} is now verified.`,
        approvePro: `${latest.name} now has Pro access.`,
        rejectPro: `${latest.name} remains on the current plan.`,
        warning: latest.status === "Blocked"
            ? `${latest.name} reached the warning limit and has been blocked.`
            : `Warning recorded for ${latest.name}.`,
        block: `${latest.name} has been blocked.`,
        unblock: `${latest.name} has been unblocked.`
    };
    showToast(messages[action]);
}

function openSidebar() {
    el.app.classList.add("sidebar-open");
}

function closeSidebar() {
    el.app.classList.remove("sidebar-open");
}

function applySidebarState() {
    el.app.classList.toggle("sidebar-collapsed", state.sidebarCollapsed);
    if (!el.sidebarCollapseButton) return;
    const icon = el.sidebarCollapseButton.querySelector("i");
    el.sidebarCollapseButton.setAttribute("aria-pressed", String(state.sidebarCollapsed));
    el.sidebarCollapseButton.setAttribute("aria-label", state.sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar");
    if (icon) {
        icon.className = `bi ${state.sidebarCollapsed ? "bi-layout-sidebar" : "bi-layout-sidebar-inset"}`;
    }
}

function bindEvents() {
    document.querySelectorAll(".nav-item").forEach((button) => {
        button.addEventListener("click", () => switchSection(button.dataset.section));
    });

    el.supportSearchInput.addEventListener("input", (e) => {
        state.supportQuery = e.target.value;
        renderSupportTable();
    });
    el.supportStatusFilter.addEventListener("change", (e) => {
        state.supportStatus = e.target.value;
        renderSupportTable();
    });
    el.reportsSearchInput.addEventListener("input", (e) => {
        state.reportsQuery = e.target.value;
        renderReportsTable();
    });
    el.reportsStatusFilter.addEventListener("change", (e) => {
        state.reportsStatus = e.target.value;
        renderReportsTable();
    });
    el.usersSearchInput.addEventListener("input", (e) => {
        state.usersQuery = e.target.value;
        renderAll();
    });
    el.usersFilterTabs.addEventListener("click", (e) => {
        const button = e.target.closest("[data-user-filter]");
        if (!button) return;
        state.usersFilter = button.dataset.userFilter;
        renderAll();
    });
    el.supportTableBody.addEventListener("click", (e) => {
        const button = e.target.closest("[data-support-id]");
        if (button) openSupportModal(button.dataset.supportId);
    });
    el.reportsTableBody.addEventListener("click", (e) => {
        const button = e.target.closest("[data-report-id]");
        if (button) openReportModal(button.dataset.reportId);
    });
    el.usersTableBody.addEventListener("click", (e) => {
        const row = e.target.closest("[data-user-select]");
        if (!row) return;
        state.selectedUserId = row.dataset.userSelect;
        renderAll();
    });

    el.panelVerifyButton.addEventListener("click", async () => { try { await userAction("verify"); } catch (error) { showToast(error.message); } });
    el.panelProPrimaryButton.addEventListener("click", async () => { try { await userAction("approvePro"); } catch (error) { showToast(error.message); } });
    el.panelProSecondaryButton.addEventListener("click", async () => { try { await userAction("rejectPro"); } catch (error) { showToast(error.message); } });
    el.panelWarningButton.addEventListener("click", async () => { try { await userAction("warning"); } catch (error) { showToast(error.message); } });
    el.panelBlockButton.addEventListener("click", async () => {
        try {
            await userAction(selectedUser()?.status === "Blocked" ? "unblock" : "block");
        } catch (error) {
            showToast(error.message);
        }
    });
    el.selectedUserProfileButton.addEventListener("click", () => {
        const user = selectedUser();
        if (user?.profileUrl) window.location.href = user.profileUrl;
    });
    el.sendReplyButton.addEventListener("click", async () => { try { await saveReply(); } catch (error) { showToast(error.message); } });
    el.markAnsweredButton.addEventListener("click", async () => { try { await markAnswered(); } catch (error) { showToast(error.message); } });
    el.markReviewedButton.addEventListener("click", async () => { try { await markReviewed(); } catch (error) { showToast(error.message); } });

    document.querySelector(".logout-button")?.addEventListener("click", () => {
        window.location.href = "/logout/0";
    });
    el.sidebarCollapseButton?.addEventListener("click", () => {
        state.sidebarCollapsed = !state.sidebarCollapsed;
        applySidebarState();
    });
    el.sidebarOpenButton.addEventListener("click", openSidebar);
    el.sidebarCloseButton.addEventListener("click", closeSidebar);
    el.sidebarBackdrop.addEventListener("click", closeSidebar);
}

async function init() {
    currentDate();
    applySidebarState();
    bindEvents();
    switchSection("dashboard");
    try {
        await loadDashboard();
    } catch (error) {
        showToast(error.message || "Failed to load admin data.");
    }
}

init();
