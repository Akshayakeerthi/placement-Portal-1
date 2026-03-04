import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { branch: '', graduation_year: 2025, cgpa: 7.0, resume_path: '' },
      resumeFile: null,
      drives: [],
      history: [],
      message: '',
      error: '',
      section: 'dashboard',
      profileDraft: { branch: '', graduation_year: 2025, cgpa: 7.0, resume_path: '' },
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
    openEditProfile() {
      this.profileDraft = { ...this.profile };
      this.section = 'edit-profile';
      this.message = '';
      this.error = '';
    },
    cancelEditProfile() {
      this.section = 'dashboard';
      this.profileDraft = { ...this.profile };
      this.error = '';
    },
    async saveProfile() {
      this.error = '';
      try {
        const saved = await api.post('/student/profile', this.profileDraft);
        this.profile = {
          ...this.profileDraft,
          resume_path: saved.data.resume_path || this.profileDraft.resume_path || '',
        };
        this.message = 'Profile updated';
        this.section = 'dashboard';
        await this.refresh();
      } catch (e) {
        this.error = e.response?.data?.error || 'Profile update failed';
      }
    },
    onResumeChange(event) {
      this.resumeFile = event.target.files?.[0] || null;
    },
    async uploadResume() {
      if (!this.resumeFile) {
        this.error = 'Choose a file first';
        return;
      }
      this.error = '';
      const formData = new FormData();
      formData.append('resume', this.resumeFile);
      try {
        const res = await api.post('/student/resume', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        this.profile.resume_path = res.data.resume_path;
        this.profileDraft.resume_path = res.data.resume_path;
        this.message = 'Resume uploaded successfully';
      } catch (e) {
        this.error = e.response?.data?.error || 'Resume upload failed';
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
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Student Dashboard</h4>
        <div class="d-flex gap-2">
          <button v-if="section==='dashboard'" class="btn btn-outline-primary" @click="openEditProfile">Edit Profile</button>
          <button class="btn btn-outline-secondary" @click="exportCsv">Export CSV</button>
        </div>
      </div>

      <div v-if="section==='edit-profile'" class="card p-3 mb-3">
        <h6>Edit Profile</h6>
        <input class="form-control mb-2" v-model="profileDraft.branch" placeholder="Branch" />
        <input class="form-control mb-2" type="number" v-model="profileDraft.graduation_year" placeholder="Graduation Year" />
        <input class="form-control mb-2" type="number" step="0.1" v-model="profileDraft.cgpa" placeholder="CGPA" />
        <input class="form-control mb-2" v-model="profileDraft.resume_path" placeholder="Resume file path" readonly />
        <div class="d-flex gap-2 mb-2">
          <input class="form-control" type="file" @change="onResumeChange" />
          <button class="btn btn-outline-primary" @click="uploadResume">Upload Resume</button>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
          <button class="btn btn-outline-secondary" @click="cancelEditProfile">Back to Dashboard</button>
        </div>
      </div>

      <div v-else>
        <div class="card p-3 mb-3">
          <h6>Profile Snapshot</h6>
          <div class="row">
            <div class="col-md-3"><strong>Branch:</strong> {{ profile.branch || 'Not set' }}</div>
            <div class="col-md-3"><strong>Year:</strong> {{ profile.graduation_year }}</div>
            <div class="col-md-3"><strong>CGPA:</strong> {{ profile.cgpa }}</div>
            <div class="col-md-3"><strong>Resume:</strong> {{ profile.resume_path || 'Not uploaded' }}</div>
          </div>
        </div>

        <div class="card p-3 mb-3">
          <h6>Eligible Drives</h6>
          <ul class="list-group">
            <li class="list-group-item d-flex justify-content-between" v-for="d in drives" :key="d.id">
              <span>{{d.title}} - {{d.company}} ({{d.deadline}})</span>
              <button class="btn btn-sm btn-success" @click="apply(d.id)">Apply</button>
            </li>
            <li class="list-group-item text-muted text-center" v-if="!drives.length">No eligible drives available</li>
          </ul>
        </div>

        <div class="card p-3">
          <h6>Application History</h6>
          <ul class="list-group">
            <li class="list-group-item" v-for="h in history" :key="h.application_id">{{h.drive_title}} - {{h.status}}</li>
            <li class="list-group-item text-muted text-center" v-if="!history.length">No application history yet</li>
          </ul>
        </div>
      </div>

      <div class="text-success mt-2">{{message}}</div>
      <div class="text-danger mt-1">{{error}}</div>
    </div>
  `,
};
