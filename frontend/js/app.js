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
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 class="mb-0">Placement Portal Application v2</h3>
          <small v-if="role">Welcome, {{name}} ({{role}})</small>
        </div>
        <button v-if="role" class="btn btn-outline-danger" @click="logout">Logout</button>
      </div>
      <AuthView v-if="!role" @logged-in="onLoggedIn" />
      <AdminDashboard v-else-if="role==='ADMIN'" />
      <CompanyDashboard v-else-if="role==='COMPANY'" />
      <StudentDashboard v-else />
    </div>
  `,
}).mount('#app');
