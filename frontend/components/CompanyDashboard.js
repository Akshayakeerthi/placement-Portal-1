import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { company_name: '', website: '', description: '' },
      profileDraft: { company_name: '', website: '', description: '' },
      drive: { title: '', description: '', eligible_branches: '', min_cgpa: 6.0, graduation_year: 2025, deadline: '' },
      drives: [],
      applicants: [],
      selectedDriveId: '',
      section: 'dashboard',
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
    openEditProfile() {
      this.profileDraft = { ...this.profile };
      this.section = 'edit-profile';
      this.error = '';
    },
    cancelEditProfile() {
      this.section = 'dashboard';
      this.error = '';
    },
    async saveProfile() {
      await api.post('/company/profile', this.profileDraft);
      this.profile = { ...this.profileDraft };
      this.message = 'Profile submitted for admin approval';
      this.section = 'dashboard';
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
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Company Dashboard</h4>
        <button v-if="section==='dashboard'" class="btn btn-outline-primary" @click="openEditProfile">Edit Profile</button>
      </div>

      <div v-if="section==='edit-profile'" class="card p-3 mb-3">
        <h6>Edit Company Profile</h6>
        <label class="form-label">Company Name</label>
        <input class="form-control mb-2" v-model="profileDraft.company_name" placeholder="Enter company name" />
        <label class="form-label">Company Website</label>
        <input class="form-control mb-2" v-model="profileDraft.website" placeholder="https://example.com" />
        <label class="form-label">Company Description</label>
        <textarea class="form-control mb-2" v-model="profileDraft.description" placeholder="Describe your company"></textarea>
        <div class="d-flex gap-2">
          <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
          <button class="btn btn-outline-secondary" @click="cancelEditProfile">Back to Dashboard</button>
        </div>
      </div>

      <div v-else>
        <div class="card p-3 mb-3">
          <h6>Company Profile Snapshot</h6>
          <div class="row">
            <div class="col-md-4"><strong>Name:</strong> {{ profile.company_name || 'Not set' }}</div>
            <div class="col-md-4"><strong>Website:</strong> {{ profile.website || 'Not set' }}</div>
            <div class="col-md-4"><strong>Description:</strong> {{ profile.description || 'Not set' }}</div>
          </div>
        </div>

        <div class="card p-3 mb-3">
          <h6>Create Drive</h6>
          <label class="form-label">Drive Title</label>
          <input class="form-control mb-2" v-model="drive.title" placeholder="e.g. Software Engineer" />
          <label class="form-label">Drive Description</label>
          <textarea class="form-control mb-2" v-model="drive.description" placeholder="Role details"></textarea>
          <label class="form-label">Eligible Branches (comma separated)</label>
          <input class="form-control mb-2" v-model="drive.eligible_branches" placeholder="CSE, ECE, IT" />
          <label class="form-label">Minimum CGPA</label>
          <input class="form-control mb-2" type="number" step="0.1" v-model="drive.min_cgpa" placeholder="e.g. 7.0" />
          <label class="form-label">Eligible Graduation Year</label>
          <input class="form-control mb-2" type="number" v-model="drive.graduation_year" placeholder="e.g. 2026" />
          <label class="form-label">Application Deadline</label>
          <input class="form-control mb-2" type="datetime-local" v-model="drive.deadline" />
          <button class="btn btn-success" @click="createDrive">Create Drive</button>
        </div>

        <div class="card p-3 mt-3">
          <h6>Your Drives</h6>
          <label class="form-label">Select Drive to View Applicants</label>
          <select class="form-select mb-2" v-model="selectedDriveId" @change="loadApplicants">
            <option value="">Select drive</option>
            <option v-for="d in drives" :key="d.id" :value="d.id">{{d.title}} | approved: {{d.approved}}</option>
          </select>
          <ul class="list-group">
            <li class="list-group-item" v-for="a in applicants" :key="a.application_id">{{a.student_name}} - {{a.status}}</li>
            <li class="list-group-item text-muted text-center" v-if="!applicants.length">No applicants yet</li>
          </ul>
        </div>
      </div>

      <div class="text-success">{{message}}</div>
      <div class="text-danger">{{error}}</div>
    </div>
  `,
};
