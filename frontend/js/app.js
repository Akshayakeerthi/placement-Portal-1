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
    };
  },
  methods: {
    onLoggedIn(role) {
      this.role = role;
      this.name = localStorage.getItem('name') || 'User';
    },
    logout() {
      localStorage.clear();
      this.role = null;
      this.name = 'User';
    },
  },
  template: `
    <div>
      <div class="top-gradient p-4 mb-4 shadow-sm">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h2 class="mb-1">Placement Portal Application</h2>
            <p class="mb-0 opacity-75">Premium dashboard experience for students, companies, and admins.</p>
            <small v-if="role" class="d-block mt-2">Welcome, {{name}} ({{role}})</small>
          </div>
          <button v-if="role" class="btn btn-light text-danger" @click="logout">Logout</button>
        </div>
      </div>

      <AuthView v-if="!role" @logged-in="onLoggedIn" />
      <AdminDashboard v-else-if="role==='ADMIN'" />
      <CompanyDashboard v-else-if="role==='COMPANY'" />
      <StudentDashboard v-else />
    </div>
  `,
}).mount('#app');
