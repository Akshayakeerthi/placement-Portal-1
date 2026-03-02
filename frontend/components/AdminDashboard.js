import api from '../services/api.js';

export default {
  data() {
    return {
      counts: {},
      q: '',
      students: [],
      companies: [],
      message: '',
    };
  },
  async mounted() {
    await this.loadDashboard();
  },
  methods: {
    async loadDashboard() {
      this.counts = (await api.get('/admin/dashboard')).data;
    },
    async searchStudents() {
      this.students = (await api.get('/admin/students', { params: { q: this.q } })).data;
    },
    async searchCompanies() {
      this.companies = (await api.get('/admin/companies', { params: { q: this.q } })).data;
    },
    async toggleBlacklist(userId, val) {
      await api.patch(`/admin/users/${userId}/blacklist`, { is_blacklisted: val });
      this.message = 'Blacklist updated';
      await this.searchStudents();
      await this.searchCompanies();
    },
  },
  template: `
    <div>
      <h4>Admin Dashboard</h4>
      <div class="row g-2 mb-3">
        <div class="col-md-3" v-for="(v,k) in counts" :key="k"><div class="card p-2"><small>{{k}}</small><h5>{{v}}</h5></div></div>
      </div>
      <div class="input-group mb-3">
        <input class="form-control" v-model="q" placeholder="Search students or companies"/>
        <button class="btn btn-outline-primary" @click="searchStudents">Students</button>
        <button class="btn btn-outline-secondary" @click="searchCompanies">Companies</button>
      </div>
      <h6>Students</h6>
      <table class="table table-sm table-bordered"><thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>Action</th></tr></thead>
      <tbody><tr v-for="s in students" :key="s.user_id"><td>{{s.name}}</td><td>{{s.email}}</td><td>{{s.branch}}</td><td><button class="btn btn-sm btn-warning" @click="toggleBlacklist(s.user_id, !s.blacklisted)">{{s.blacklisted?'Unblacklist':'Blacklist'}}</button></td></tr></tbody></table>
      <h6>Companies</h6>
      <table class="table table-sm table-bordered"><thead><tr><th>Company</th><th>Email</th><th>Approved</th></tr></thead>
      <tbody><tr v-for="c in companies" :key="c.company_id"><td>{{c.company_name}}</td><td>{{c.email}}</td><td>{{c.approved}}</td></tr></tbody></table>
      <div class="text-success">{{message}}</div>
    </div>
  `,
};
