import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { company_name: '', website: '', description: '' },
      drive: { title: '', description: '', eligible_branches: '', min_cgpa: 6.0, graduation_year: 2025, deadline: '' },
      drives: [],
      applicants: [],
      selectedDriveId: '',
      message: '',
      error: '',
    };
  },
  async mounted() {
    await this.loadDrives();
  },
  methods: {
    async loadDrives() {
      this.drives = (await api.get('/company/drives')).data;
    },
    async saveProfile() {
      await api.post('/company/profile', this.profile);
      this.message = 'Profile submitted for admin approval';
    },
    async createDrive() {
      this.error = '';
      try {
        await api.post('/company/drives', {
          ...this.drive,
          eligible_branches: this.drive.eligible_branches.split(',').map((v) => v.trim()).filter(Boolean),
        });
        this.message = 'Drive submitted for approval';
        await this.loadDrives();
      } catch (e) {
        this.error = e.response?.data?.error || 'Could not create drive';
      }
    },
    async loadApplicants() {
      if (!this.selectedDriveId) return;
      this.applicants = (await api.get(`/company/drives/${this.selectedDriveId}/applicants`)).data;
    },
  },
  template: `
    <div>
      <h4>Company Dashboard</h4>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="card p-3">
            <h6>Company Profile</h6>
            <input class="form-control mb-2" v-model="profile.company_name" placeholder="Company name" />
            <input class="form-control mb-2" v-model="profile.website" placeholder="Website" />
            <textarea class="form-control mb-2" v-model="profile.description" placeholder="Description"></textarea>
            <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3">
            <h6>Create Drive</h6>
            <input class="form-control mb-2" v-model="drive.title" placeholder="Title" />
            <textarea class="form-control mb-2" v-model="drive.description" placeholder="Description"></textarea>
            <input class="form-control mb-2" v-model="drive.eligible_branches" placeholder="CSE,ECE,IT" />
            <input class="form-control mb-2" type="number" v-model="drive.min_cgpa" />
            <input class="form-control mb-2" type="number" v-model="drive.graduation_year" />
            <input class="form-control mb-2" type="datetime-local" v-model="drive.deadline" />
            <button class="btn btn-success" @click="createDrive">Create Drive</button>
          </div>
        </div>
      </div>
      <div class="card p-3 mt-3">
        <h6>Your Drives</h6>
        <select class="form-select mb-2" v-model="selectedDriveId" @change="loadApplicants">
          <option value="">Select drive</option>
          <option v-for="d in drives" :key="d.id" :value="d.id">{{d.title}} | approved: {{d.approved}}</option>
        </select>
        <ul class="list-group"><li class="list-group-item" v-for="a in applicants" :key="a.application_id">{{a.student_name}} - {{a.status}}</li></ul>
      </div>
      <div class="text-success">{{message}}</div>
      <div class="text-danger">{{error}}</div>
    </div>
  `,
};
