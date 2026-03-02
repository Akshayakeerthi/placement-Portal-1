import AuthView from '../components/AuthView.js';
import AdminDashboard from '../components/AdminDashboard.js';
import CompanyDashboard from '../components/CompanyDashboard.js';
import StudentDashboard from '../components/StudentDashboard.js';

const { createApp } = Vue;

createApp({
  components: { AuthView, AdminDashboard, CompanyDashboard, StudentDashboard },
  data() {
    return { role: localStorage.getItem('role') || null };
  },
  methods: {
    onAuth(role) {
      this.role = role;
    },
    logout() {
      localStorage.clear();
      this.role = null;
    },
  },
  template: `
    <div>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">Placement Portal Application v2</h2>
        <button v-if="role" class="btn btn-outline-danger" @click="logout">Logout</button>
      </div>
      <AuthView v-if="!role" :onAuth="onAuth" />
      <AdminDashboard v-else-if="role==='ADMIN'" />
      <CompanyDashboard v-else-if="role==='COMPANY'" />
      <StudentDashboard v-else />
    </div>
  `,
}).mount('#app');
