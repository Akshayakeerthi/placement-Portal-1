import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { branch: '', graduation_year: new Date().getFullYear(), cgpa: 0, resume_path: '' },
      resumeFile: null,
      history: [],
      message: '',
      error: '',
      section: 'dashboard',
      profileDraft: { branch: '', graduation_year: new Date().getFullYear(), cgpa: 0, resume_path: '' },
      drivesPage: { items: [], page: 1, per_page: 5, total: 0, total_pages: 1 },
      fitProfile: false,
      selectedDrive: null,
    };
  },
  async mounted() {
    await this.loadProfile();
    await this.refresh();
  },
  methods: {
    async loadProfile() {
      const data = (await api.get('/student/profile')).data;
      this.profile = {
        branch: data.branch || '',
        graduation_year: data.graduation_year || new Date().getFullYear(),
        cgpa: data.cgpa || 0,
        resume_path: data.resume_path || '',
      };
      this.profileDraft = { ...this.profile };
    },
    async refresh() {
      try {
        await this.loadDrives(this.drivesPage.page);
        this.history = (await api.get('/student/applications')).data;
      } catch {
        this.drivesPage = { items: [], page: 1, per_page: 5, total: 0, total_pages: 1 };
        this.history = [];
      }
    },
    async loadDrives(page = 1) {
      const res = await api.get('/student/drives', {
        params: { fit_profile: this.fitProfile, page, per_page: this.drivesPage.per_page },
      });
      this.drivesPage = res.data;
    },
    async toggleFitProfile() {
      await this.loadDrives(1);
    },
    async gotoPage(page) {
      if (page < 1 || page > this.drivesPage.total_pages) return;
      await this.loadDrives(page);
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
    viewDriveDetails(drive) {
      this.selectedDrive = drive;
    },
    clearDriveDetails() {
      this.selectedDrive = null;
    },
    statusLabel(status) {
      const labels = {
        APPLIED: 'Pending Action',
        SHORTLISTED: 'Shortlisted',
        SELECTED: 'Selected',
        REJECTED: 'Rejected',
        INTERVIEW_SCHEDULED: 'Interview Scheduled',
      };
      return labels[status] || status;
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
        <label class="form-label">Branch</label>
        <input class="form-control mb-2" v-model="profileDraft.branch" placeholder="e.g. CSE" />
        <label class="form-label">Graduation Year</label>
        <input class="form-control mb-2" type="number" v-model="profileDraft.graduation_year" placeholder="e.g. 2022, 2025, 2026" />
        <label class="form-label">CGPA</label>
        <input class="form-control mb-2" type="number" step="0.1" v-model="profileDraft.cgpa" placeholder="e.g. 8.1" />
        <label class="form-label">Resume Path</label>
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
          <div class="d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Available Drives</h6>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="fitProfileCheck" v-model="fitProfile" @change="toggleFitProfile" />
              <label class="form-check-label" for="fitProfileCheck">Filter to fit profile</label>
            </div>
          </div>
          <ul class="list-group mt-2">
            <li class="list-group-item d-flex justify-content-between align-items-center" v-for="d in drivesPage.items" :key="d.id">
              <div>
                <div><strong>{{d.title}}</strong> - {{d.company.name}}</div>
                <small class="text-muted">Deadline: {{d.deadline}} | Min CGPA: {{d.min_cgpa}} | Max Passing Year: {{d.graduation_year}}</small>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-primary" @click="viewDriveDetails(d)">View Details</button>
                <button class="btn btn-sm btn-success" :disabled="!d.eligible" @click="apply(d.id)">Apply</button>
              </div>
            </li>
            <li class="list-group-item text-muted text-center" v-if="!drivesPage.items.length">No drives available</li>
          </ul>
          <div class="d-flex justify-content-center gap-2 mt-3" v-if="drivesPage.total_pages > 1">
            <button class="btn btn-sm btn-outline-secondary" @click="gotoPage(drivesPage.page-1)">Prev</button>
            <button class="btn btn-sm"
              :class="p===drivesPage.page ? 'btn-primary':'btn-outline-primary'"
              v-for="p in drivesPage.total_pages" :key="p" @click="gotoPage(p)">{{p}}</button>
            <button class="btn btn-sm btn-outline-secondary" @click="gotoPage(drivesPage.page+1)">Next</button>
          </div>
        </div>

        <div class="card p-3 mb-3" v-if="selectedDrive">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Drive Details</h6>
            <button class="btn btn-sm btn-outline-secondary" @click="clearDriveDetails">Close</button>
          </div>
          <p class="mb-1"><strong>Title:</strong> {{selectedDrive.title}}</p>
          <p class="mb-1"><strong>Description:</strong> {{selectedDrive.description}}</p>
          <p class="mb-1"><strong>Eligibility:</strong> Branches {{selectedDrive.eligible_branches}}, CGPA >= {{selectedDrive.min_cgpa}}, Passing Year <= {{selectedDrive.graduation_year}}</p>
          <p class="mb-1"><strong>Company:</strong> {{selectedDrive.company.name}}</p>
          <p class="mb-1"><strong>Company Website:</strong> {{selectedDrive.company.website || 'N/A'}}</p>
          <p class="mb-0"><strong>Company Description:</strong> {{selectedDrive.company.description || 'N/A'}}</p>
        </div>

        <div class="card p-3">
          <h6>Application History</h6>
          <ul class="list-group">
            <li class="list-group-item" v-for="h in history" :key="h.application_id">{{h.drive_title}} - {{statusLabel(h.status)}}</li>
            <li class="list-group-item text-muted text-center" v-if="!history.length">No application history yet</li>
          </ul>
        </div>
      </div>

      <div class="text-success mt-2">{{message}}</div>
      <div class="text-danger mt-1">{{error}}</div>
    </div>
  `,
};
