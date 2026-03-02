import api from '../services/api.js';

export default {
  data() {
    return { counts: {}, query: '', students: [], companies: [] };
  },
  async mounted() {
    const res = await api.get('/admin/dashboard');
    this.counts = res.data;
  },
  methods: {
    async searchStudents() {
      const res = await api.get('/admin/students', { params: { q: this.query } });
      this.students = res.data;
    },
    async searchCompanies() {
      const res = await api.get('/admin/companies', { params: { q: this.query } });
      this.companies = res.data;
    },
  },
  template: `
  <div>
    <h3>Admin Dashboard</h3>
    <div class="row g-2 my-2">
      <div class="col" v-for="(v,k) in counts" :key="k"><div class="card p-2"><small>{{k}}</small><h5>{{v}}</h5></div></div>
    </div>
    <div class="input-group my-3">
      <input class="form-control" v-model="query" placeholder="Search">
      <button class="btn btn-outline-primary" @click="searchStudents">Students</button>
      <button class="btn btn-outline-secondary" @click="searchCompanies">Companies</button>
    </div>
  </div>
  `,
};
