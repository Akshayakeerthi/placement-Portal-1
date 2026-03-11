import api from '../services/api.js';

export default {
  data() {
    return {
      counts: {},
      summary: {},
      trends: { drives: [], applications: [] },
      applicationStatusSummary: {},
      q: '',
      students: [],
      companies: [],
      drives: [],
      message: '',
      error: '',
      loading: false,
      exportingSummary: false,
      activeMainTab: 'dashboard',
      activeDataTab: 'students',
      selectedDrive: null,
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
        await Promise.all([
          this.loadDashboard(),
          this.searchStudents(),
          this.searchCompanies(),
          this.loadDrives(),
        ]);
      } catch (e) {
        this.error = e.response?.data?.error || 'Could not refresh admin dashboard';
      } finally {
        this.loading = false;
      }
    },
    async loadDashboard() {
      const payload = (await api.get('/admin/dashboard')).data;
      this.counts = payload.counts || {};
      this.summary = payload.summary || {};
      this.trends = payload.trends || { drives: [], applications: [] };
      this.applicationStatusSummary = payload.application_status_summary || {};
    },
    async searchStudents() {
      this.students = (await api.get('/admin/students', { params: { q: this.q } })).data;
    },
    async searchCompanies() {
      this.companies = (await api.get('/admin/companies', { params: { q: this.q } })).data;
    },
    async loadDrives() {
      this.drives = (await api.get('/admin/drives', { params: { q: this.q } })).data;
    },
    async onSearchInput() {
      await Promise.all([this.searchStudents(), this.searchCompanies(), this.loadDrives()]);
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
    async setDriveApproval(driveId, approved) {
      await api.patch(`/admin/drives/${driveId}/approval`, { approved });
      this.message = approved ? 'Drive approved' : 'Drive rejected';
      await this.refreshAll();
    },
    async closeDrive(driveId) {
      await api.patch(`/admin/drives/${driveId}/close`);
      this.message = 'Drive closed';
      await this.refreshAll();
    },
    async exportSummary() {
      this.exportingSummary = true;
      this.error = '';
      try {
        const res = await api.post('/admin/summary/export');
        this.message = res.data?.message || 'Summary export started and email will be sent to admin';
      } catch (e) {
        this.error = e.response?.data?.error || 'Could not export summary';
      } finally {
        this.exportingSummary = false;
      }
    },
    viewDriveDetails(drive) {
      this.selectedDrive = drive;
    },
    maxTrendCount(items = []) {
      if (!items.length) return 1;
      return Math.max(...items.map((x) => x.count || 0), 1);
    },
  },
  template: `
    <div class="glass-card p-3 p-md-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="section-title mb-0">Admin Dashboard</h4>
        <button class="btn btn-outline-secondary btn-sm" @click="refreshAll">Refresh</button>
      </div>

      <ul class="nav nav-pills mb-3">
        <li class="nav-item"><button class="nav-link" :class="{active: activeMainTab==='dashboard'}" @click="activeMainTab='dashboard'">Dashboard</button></li>
        <li class="nav-item"><button class="nav-link" :class="{active: activeMainTab==='summary'}" @click="activeMainTab='summary'">Summary</button></li>
      </ul>

      <div v-if="activeMainTab==='summary'" class="card border-0 shadow-sm mb-3">
        <div class="card-body">
          <div class="d-flex flex-wrap justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Placement Summary</h6>
            <div class="d-flex gap-2">
              <span class="badge text-bg-info">Admin only</span>
              <button class="btn btn-sm btn-primary" :disabled="exportingSummary" @click="exportSummary">
                {{ exportingSummary ? 'Exporting...' : 'Export' }}
              </button>
            </div>
          </div>
          <div class="row g-2 mb-2">
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Companies</small><div class="fw-semibold">{{counts.companies || 0}}</div></div></div>
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Students</small><div class="fw-semibold">{{counts.students || 0}}</div></div></div>
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Drives</small><div class="fw-semibold">{{counts.drives || 0}}</div></div></div>
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Applications</small><div class="fw-semibold">{{counts.applications || 0}}</div></div></div>
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Pending Companies</small><div class="fw-semibold">{{summary.pending_companies || 0}}</div></div></div>
            <div class="col-6 col-lg-2"><div class="p-2 bg-light rounded"><small class="text-muted">Selection Rate</small><div class="fw-semibold">{{summary.selection_rate || 0}}%</div></div></div>
          </div>
          <div class="row g-3">
            <div class="col-lg-6">
              <small class="text-muted d-block mb-1">Drive creation trend (6 months)</small>
              <div v-for="t in trends.drives" :key="'d-'+t.month" class="d-flex align-items-center gap-2 mb-1">
                <small style="width:68px">{{t.month}}</small>
                <div class="progress flex-grow-1" style="height:8px">
                  <div class="progress-bar bg-primary" :style="{ width: ((t.count / maxTrendCount(trends.drives)) * 100) + '%' }"></div>
                </div>
                <small class="fw-semibold" style="width:20px">{{t.count}}</small>
              </div>
            </div>
            <div class="col-lg-6">
              <small class="text-muted d-block mb-1">Application trend (6 months)</small>
              <div v-for="t in trends.applications" :key="'a-'+t.month" class="d-flex align-items-center gap-2 mb-1">
                <small style="width:68px">{{t.month}}</small>
                <div class="progress flex-grow-1" style="height:8px">
                  <div class="progress-bar bg-success" :style="{ width: ((t.count / maxTrendCount(trends.applications)) * 100) + '%' }"></div>
                </div>
                <small class="fw-semibold" style="width:20px">{{t.count}}</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template v-if="activeMainTab==='dashboard'">
        <div class="row g-3 mb-3">
          <div class="col-6 col-lg-3" v-for="(v,k) in counts" :key="k">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <small class="text-muted text-uppercase">{{k}}</small>
                <h5 class="mb-0 mt-1">{{v}}</h5>
              </div>
            </div>
          </div>
        </div>

        <div class="input-group mb-3">
          <span class="input-group-text">🔎</span>
          <input class="form-control" v-model="q" @input="onSearchInput" placeholder="Search students, companies, or drives"/>
        </div>

        <ul class="nav nav-pills mb-3">
          <li class="nav-item"><button class="nav-link" :class="{active: activeDataTab==='students'}" @click="activeDataTab='students'">Students</button></li>
          <li class="nav-item"><button class="nav-link" :class="{active: activeDataTab==='companies'}" @click="activeDataTab='companies'">Companies</button></li>
          <li class="nav-item"><button class="nav-link" :class="{active: activeDataTab==='drives'}" @click="activeDataTab='drives'">Drives</button></li>
        </ul>

        <div v-if="loading" class="alert alert-info py-2">Refreshing data...</div>
        <div v-if="error" class="alert alert-danger py-2">{{error}}</div>

        <div class="card shadow-sm mb-3" v-if="activeDataTab==='students'">
          <div class="card-header fw-semibold">Registered Students</div>
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-if="!students.length"><td colspan="6" class="text-center text-muted">No students found</td></tr>
                <tr v-for="s in students" :key="s.user_id">
                  <td>{{s.name}}</td><td>{{s.email}}</td><td>{{s.branch}}</td><td>{{s.cgpa}}</td><td>{{s.graduation_year}}</td>
                  <td><button class="btn btn-sm btn-warning" @click="toggleBlacklist(s.user_id, !s.blacklisted)">{{s.blacklisted?'Unblacklist':'Blacklist'}}</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card shadow-sm mb-3" v-if="activeDataTab==='companies'">
          <div class="card-header fw-semibold">Registered Companies</div>
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead><tr><th>Company</th><th>Email</th><th>Approved</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-if="!companies.length"><td colspan="4" class="text-center text-muted">No companies found</td></tr>
                <tr v-for="c in companies" :key="c.company_id">
                  <td>{{c.company_name}}</td>
                  <td>{{c.email}}</td>
                  <td><span class="badge status-badge" :class="c.approved ? 'text-bg-success' : 'text-bg-secondary'">{{ c.approved ? 'Approved' : 'Pending' }}</span></td>
                  <td class="d-flex gap-1">
                    <template v-if="!c.approved">
                      <button class="btn btn-sm btn-success" @click="setCompanyApproval(c.company_id, true)">Approve</button>
                      <button class="btn btn-sm btn-outline-danger" @click="setCompanyApproval(c.company_id, false)">Reject</button>
                    </template>
                    <button class="btn btn-sm btn-warning" @click="toggleBlacklist(c.user_id, !c.blacklisted)">{{c.blacklisted?'Unblacklist':'Blacklist'}}</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card shadow-sm" v-if="activeDataTab==='drives'">
          <div class="card-header fw-semibold">Placement Drives</div>
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead><tr><th>Drive</th><th>Company</th><th>Deadline</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-if="!drives.length"><td colspan="5" class="text-center text-muted">No drives found</td></tr>
                <tr v-for="d in drives" :key="d.drive_id">
                  <td>{{d.title}}</td>
                  <td>{{d.company_name}}</td>
                  <td>{{d.deadline}}</td>
                  <td><span class="badge status-badge" :class="d.closed ? 'text-bg-dark' : (d.approved ? 'text-bg-success' : 'text-bg-secondary')">{{ d.closed ? 'Closed' : (d.approved ? 'Approved' : 'Pending') }}</span></td>
                  <td class="d-flex gap-1 flex-wrap">
                    <template v-if="!d.approved && !d.closed">
                      <button class="btn btn-sm btn-success" @click="setDriveApproval(d.drive_id, true)">Approve</button>
                      <button class="btn btn-sm btn-outline-danger" @click="setDriveApproval(d.drive_id, false)">Reject</button>
                    </template>
                    <button class="btn btn-sm btn-outline-primary" @click="viewDriveDetails(d)">View Details</button>
                    <button v-if="d.approved && !d.closed" class="btn btn-sm btn-outline-dark" @click="closeDrive(d.drive_id)">Close Drive</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card mt-3 shadow-sm" v-if="activeDataTab==='drives' && selectedDrive">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">Drive Details</span>
            <button class="btn btn-sm btn-outline-secondary" @click="selectedDrive=null">Close</button>
          </div>
          <div class="card-body">
            <p class="mb-1"><strong>Title:</strong> {{selectedDrive.title}}</p>
            <p class="mb-1"><strong>Description:</strong> {{selectedDrive.description}}</p>
            <p class="mb-1"><strong>Eligibility:</strong> Branches {{selectedDrive.eligible_branches}}, CGPA >= {{selectedDrive.min_cgpa}}, Passing Year <= {{selectedDrive.graduation_year}}</p>
            <p class="mb-1"><strong>Company:</strong> {{selectedDrive.company_name}}</p>
            <p class="mb-1"><strong>Company Website:</strong> {{selectedDrive.company_website || 'N/A'}}</p>
            <p class="mb-0"><strong>Company Description:</strong> {{selectedDrive.company_description || 'N/A'}}</p>
          </div>
        </div>
      </template>

      <div class="alert alert-success py-2 mt-3 mb-0" v-if="message">{{message}}</div>
      <div class="alert alert-danger py-2 mt-3 mb-0" v-if="activeMainTab==='summary' && error">{{error}}</div>
    </div>
  `,
};
