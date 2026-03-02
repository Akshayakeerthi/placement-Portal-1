import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { branch: '', graduation_year: 2025, cgpa: 7.5, resume_path: '' },
      drives: [],
      history: [],
      msg: '',
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
      }
    },
    async saveProfile() {
      await api.post('/student/profile', this.profile);
      this.msg = 'Profile updated';
      await this.refresh();
    },
    async apply(id) {
      await api.post(`/student/drives/${id}/apply`);
      this.msg = 'Applied successfully';
      await this.refresh();
    },
    async exportCsv() {
      await api.post('/student/applications/export');
      this.msg = 'Export task queued';
    },
  },
  template: `
  <div>
    <h3>Student Dashboard</h3>
    <div class="card p-3 mb-3">
      <h5>Profile</h5>
      <input class="form-control mb-2" v-model="profile.branch" placeholder="Branch"/>
      <input class="form-control mb-2" type="number" v-model="profile.graduation_year" placeholder="Graduation Year"/>
      <input class="form-control mb-2" type="number" step="0.1" v-model="profile.cgpa" placeholder="CGPA"/>
      <input class="form-control mb-2" v-model="profile.resume_path" placeholder="Resume path (local storage path)"/>
      <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
      <button class="btn btn-outline-secondary ms-2" @click="exportCsv">Export CSV</button>
    </div>
    <h5>Eligible Drives</h5>
    <ul class="list-group mb-3">
      <li class="list-group-item d-flex justify-content-between" v-for="d in drives" :key="d.id">
        {{d.title}} - {{d.company}} <button class="btn btn-sm btn-success" @click="apply(d.id)">Apply</button>
      </li>
    </ul>
    <h5>Application History</h5>
    <ul class="list-group"><li class="list-group-item" v-for="h in history" :key="h.application_id">{{h.drive}} - {{h.status}}</li></ul>
    <div class="text-success mt-2">{{msg}}</div>
  </div>
  `,
};
