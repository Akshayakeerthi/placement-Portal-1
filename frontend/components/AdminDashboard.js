import api from '../services/api.js';

export default {
  data() {
    return {
      counts: {},
      q: '',
      students: [],
      companies: [],
      message: '',
      error: '',
      loading: false,
    };
  },
  async mounted() {
    await this.refreshAll();
  },
  methods: {
    async refreshAll() {
      this.loading = true;
      this.error = '';
      try {
        await Promise.all([this.loadDashboard(), this.searchStudents(), this.searchCompanies()]);
      } catch (e) {
        this.error = e.response?.data?.error || 'Could not refresh admin dashboard';
      } finally {
        this.loading = false;
      }
    },
    async loadDashboard() {
      this.counts = (await api.get('/admin/dashboard')).data;
    },
    async searchStudents() {
      this.students = (await api.get('/admin/students', { params: { q: this.q } })).data;
    },
    async searchCompanies() {
      this.companies = (await api.get('/admin/companies', { params: { q: this.q } })).data;
    },
    async onSearchInput() {
      await Promise.all([this.searchStudents(), this.searchCompanies()]);
    },
    async toggleBlacklist(userId, val) {
      await api.patch(`/admin/users/${userId}/blacklist`, { is_blacklisted: val });
      this.message = 'Blacklist updated';
      await this.refreshAll();
    },
    async setCompanyApproval(companyId, approved) {
      await api.patch(`/admin/companies/${companyId}/approval`, { approved });
      this.message = approved ? 'Company approved' : 'Company rejected';
      await this.refreshAll();
    },
  },
  template: `
    <div>
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h4 class="mb-0">Admin Dashboard</h4>
        <button class="btn btn-sm btn-outline-secondary" @click="refreshAll">Refresh</button>
      </div>

      <div class="row g-2 mb-3">
        <div class="col-md-3" v-for="(v,k) in counts" :key="k">
          <div class="card p-2 h-100">
            <small class="text-muted text-uppercase">{{k}}</small>
            <h5 class="mb-0">{{v}}</h5>
          </div>
        </div>
      </div>

      <div class="input-group mb-3">
        <input class="form-control" v-model="q" @input="onSearchInput" placeholder="Search students or companies"/>
        <button class="btn btn-outline-primary" @click="searchStudents">Students</button>
        <button class="btn btn-outline-secondary" @click="searchCompanies">Companies</button>
      </div>

      <div v-if="loading" class="alert alert-info py-2">Refreshing data...</div>
      <div v-if="error" class="alert alert-danger py-2">{{error}}</div>

      <div class="card mb-3">
        <div class="card-header">Registered Students</div>
        <div class="table-responsive">
          <table class="table table-sm table-bordered mb-0">
            <thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>Action</th></tr></thead>
            <tbody>
              <tr v-if="!students.length"><td colspan="4" class="text-center text-muted">No students found</td></tr>
              <tr v-for="s in students" :key="s.user_id">
                <td>{{s.name}}</td><td>{{s.email}}</td><td>{{s.branch}}</td>
                <td>
                  <button class="btn btn-sm btn-warning" @click="toggleBlacklist(s.user_id, !s.blacklisted)">
                    {{s.blacklisted?'Unblacklist':'Blacklist'}}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">Registered Companies</div>
        <div class="table-responsive">
          <table class="table table-sm table-bordered mb-0">
            <thead><tr><th>Company</th><th>Email</th><th>Approved</th><th>Action</th></tr></thead>
            <tbody>
              <tr v-if="!companies.length"><td colspan="4" class="text-center text-muted">No companies found</td></tr>
              <tr v-for="c in companies" :key="c.company_id">
                <td>{{c.company_name}}</td>
                <td>{{c.email}}</td>
                <td>
                  <span class="badge" :class="c.approved ? 'text-bg-success' : 'text-bg-secondary'">
                    {{ c.approved ? 'Approved' : 'Pending' }}
                  </span>
                </td>
                <td class="d-flex gap-1">
                  <button class="btn btn-sm btn-success" @click="setCompanyApproval(c.company_id, true)">Approve</button>
                  <button class="btn btn-sm btn-outline-danger" @click="setCompanyApproval(c.company_id, false)">Reject</button>
                  <button class="btn btn-sm btn-warning" @click="toggleBlacklist(c.user_id, !c.blacklisted)">
                    {{c.blacklisted?'Unblacklist':'Blacklist'}}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="text-success mt-2">{{message}}</div>
    </div>
  `,
};
