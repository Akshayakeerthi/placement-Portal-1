import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { branch: '', graduation_year: 2025, cgpa: 7.0, resume_path: '' },
      drives: [],
      history: [],
      message: '',
      error: '',
    };
  },
  async mounted() {
    await this.refresh();
  },
  methods: {
    async refresh() {
      try {
        this.drives = (await api.get('/student/drives')).data;
        this.history = (await api.get('/student/applications')).data;
      } catch {
        this.drives = [];
        this.history = [];
      }
    },
    async saveProfile() {
      this.error = '';
      try {
        await api.post('/student/profile', this.profile);
        this.message = 'Profile updated';
        await this.refresh();
      } catch (e) {
        this.error = e.response?.data?.error || 'Profile update failed';
      }
    },
    async apply(driveId) {
      try {
        await api.post(`/student/drives/${driveId}/apply`);
        this.message = 'Applied successfully';
        await this.refresh();
      } catch (e) {
        this.error = e.response?.data?.error || 'Apply failed';
      }
    },
    async exportCsv() {
      await api.post('/student/applications/export');
      this.message = 'CSV export queued';
    },
  },
  template: `
    <div>
      <h4>Student Dashboard</h4>
      <div class="card p-3 mb-3">
        <h6>Profile</h6>
        <input class="form-control mb-2" v-model="profile.branch" placeholder="Branch" />
        <input class="form-control mb-2" type="number" v-model="profile.graduation_year" placeholder="Graduation Year" />
        <input class="form-control mb-2" type="number" step="0.1" v-model="profile.cgpa" placeholder="CGPA" />
        <input class="form-control mb-2" v-model="profile.resume_path" placeholder="Resume file path" />
        <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
        <button class="btn btn-outline-secondary ms-2" @click="exportCsv">Export CSV</button>
      </div>
      <div class="card p-3 mb-3">
        <h6>Eligible Drives</h6>
        <ul class="list-group">
          <li class="list-group-item d-flex justify-content-between" v-for="d in drives" :key="d.id">
            <span>{{d.title}} - {{d.company}} ({{d.deadline}})</span>
            <button class="btn btn-sm btn-success" @click="apply(d.id)">Apply</button>
          </li>
        </ul>
      </div>
      <div class="card p-3">
        <h6>Application History</h6>
        <ul class="list-group"><li class="list-group-item" v-for="h in history" :key="h.application_id">{{h.drive_title}} - {{h.status}}</li></ul>
      </div>
      <div class="text-success mt-2">{{message}}</div>
      <div class="text-danger mt-1">{{error}}</div>
    </div>
  `,
};
