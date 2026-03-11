import AuthView from '../components/AuthView.js';
import AdminDashboard from '../components/AdminDashboard.js';
import CompanyDashboard from '../components/CompanyDashboard.js';
import StudentDashboard from '../components/StudentDashboard.js';

const { createApp } = Vue;

createApp({
  components: { AuthView, AdminDashboard, CompanyDashboard, StudentDashboard },
  data() {
    return {
      role: localStorage.getItem('role'),
      name: localStorage.getItem('name') || 'User',
      authRoute: null,
    };
  },
  methods: {
    onLoggedIn(role) {
      this.role = role;
      this.name = localStorage.getItem('name') || 'User';
      this.authRoute = null;
    },
    logout() {
      localStorage.clear();
      this.role = null;
      this.name = 'User';
      this.authRoute = null;
    },
    goToAuth(mode = 'login', role = 'STUDENT') {
      this.authRoute = { mode, role };
    },
    goHome() {
      this.authRoute = null;
    },
  },
  template: `
    <div>
      <template v-if="!role && !authRoute">
        <nav class="navbar navbar-dark bg-dark px-3 px-lg-5 mb-4 rounded-3">
          <span class="navbar-brand mb-0 h1">SeekerHub</span>
          <button class="btn btn-outline-light" @click="goToAuth('login', 'STUDENT')">Login</button>
        </nav>

        <section class="landing-shell p-4 p-lg-5 mb-4">
          <div class="row g-4 align-items-start">
            <div class="col-lg-8">
              <span class="badge rounded-pill text-bg-primary mb-3">Campus Recruitment Platform</span>
              <h1 class="display-5 fw-bold mb-3">SeekerHub</h1>
              <p class="lead mb-3">A single platform where institutes, students, and recruiters collaborate for smoother campus placements.</p>
              <p class="text-secondary mb-4">Inspired by modern hiring portals like Naukri, Indeed and Glassdoor, this application helps manage the full lifecycle: company approvals, drive publishing, applications, shortlisting, and final outcomes.</p>

              <div class="d-flex flex-wrap gap-2">
                <button class="btn btn-primary btn-lg px-4" @click="goToAuth('login', 'STUDENT')">Login</button>
                <button class="btn btn-success btn-lg px-4" @click="goToAuth('register', 'STUDENT')">Student Register</button>
                <button class="btn btn-info btn-lg px-4 text-dark" @click="goToAuth('register', 'COMPANY')">Company Register</button>
              </div>
            </div>
            <div class="col-lg-4">
              <div class="info-tile p-3 mb-3">
                <h4 class="h3 fw-semibold">For Companies</h4>
                <p class="mb-0">Create drives, review applicants, shortlist & close hiring.</p>
              </div>
              <div class="info-tile p-3">
                <h4 class="h3 fw-semibold">For Students</h4>
                <p class="mb-0">Discover drives, apply once, and track statuses in one place.</p>
              </div>
            </div>
          </div>
        </section>

        <section class="row g-3 mb-4">
          <div class="col-lg-4"><div class="feature-card p-3"><h3>Company Verification</h3><p class="mb-0">Admin approves only valid organizations before they can post recruitment drives.</p></div></div>
          <div class="col-lg-4"><div class="feature-card p-3"><h3>Drive Management</h3><p class="mb-0">Create, approve, complete and archive placement drives with clear visibility.</p></div></div>
          <div class="col-lg-4"><div class="feature-card p-3"><h3>Application Tracking</h3><p class="mb-0">Students and companies both see real-time application status and history.</p></div></div>
        </section>
      </template>

      <template v-else-if="!role && authRoute">
        <nav class="navbar navbar-dark bg-dark px-3 px-lg-5 mb-4 rounded-3">
          <span class="navbar-brand mb-0 h1">SeekerHub</span>
          <button class="btn btn-outline-light" @click="goHome">Back to Home</button>
        </nav>

        <AuthView
          :preset-mode="authRoute.mode"
          :preset-role="authRoute.role"
          @logged-in="onLoggedIn"
        />
      </template>

      <template v-else>
        <div class="top-gradient p-4 mb-4 shadow-sm">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h2 class="mb-1">SeekerHub Application</h2>
              <p class="mb-0 opacity-75">Dashboard for students, companies, and admins.</p>
              <small class="d-block mt-2">Welcome, {{name}} ({{role}})</small>
            </div>
            <button class="btn btn-light text-danger" @click="logout">Logout</button>
          </div>
        </div>

        <AdminDashboard v-if="role==='ADMIN'" />
        <CompanyDashboard v-else-if="role==='COMPANY'" />
        <StudentDashboard v-else />
      </template>
    </div>
  `,
}).mount('#app');
