<template>
  <main class="wrap">
    <TopBar :api-base-label="apiBaseLabel" :busy="busy" @refresh="refreshAll" />

    <section class="grid">
      <CreateCard
        :busy="busy"
        :default-software="defaultSoftware"
        :distributions="distributions"
        :error="createError"
        :reset-key="createResetKey"
        @create="onCreate"
      />
      <UploadsCard :busy="busy" :uploads="uploads" @select="selectUpload" />
    </section>

    <section class="grid" style="margin-top: 16px;">
      <SearchCard
        :busy="busy"
        :default-software="defaultSoftware"
        :results="searchResults"
        :count="searchCount"
        :error="searchError"
        :reset-key="searchResetKey"
        @search="runSearch"
        @clear="clearSearch"
        @select="selectUpload"
      />
      <ApiCard :busy="busy" :routes="routes" :error="apiError" @load="loadRoutes" />
    </section>

    <UploadDetailCard
      v-if="selected"
      class="detail"
      :busy="busy"
      :default-software="defaultSoftware"
      :upload="selected"
      :manifest="manifest"
      :error="editError"
      @save-software="onSaveSoftware"
      @load-manifest="loadManifest"
      @delete="onDelete"
    />
  </main>
</template>

<script>
import ApiCard from "../components/ApiCard.vue";
import CreateCard from "../components/CreateCard.vue";
import SearchCard from "../components/SearchCard.vue";
import TopBar from "../components/TopBar.vue";
import UploadDetailCard from "../components/UploadDetailCard.vue";
import UploadsCard from "../components/UploadsCard.vue";
import {
  createFromDistribution,
  deleteUpload,
  getDefaultSoftware,
  getDistributions,
  getInstallManifest,
  getUpload,
  listRoutes,
  listUploads,
  searchUploads,
  updateSoftware,
  uploadIso
} from "../api.js";

export default {
  components: { ApiCard, CreateCard, SearchCard, TopBar, UploadDetailCard, UploadsCard },
  data() {
    return {
      busy: false,
      defaultSoftware: [],
      distributions: [],
      uploads: [],
      routes: null,
      selectedId: null,
      selected: null,
      manifest: null,
      createError: "",
      editError: "",
      apiError: "",
      searchResults: [],
      searchCount: 0,
      searchError: "",
      createResetKey: 0,
      searchResetKey: 0
    };
  },
  computed: {
    apiBaseLabel() {
      return import.meta.env.VITE_API_BASE || "(same origin)";
    }
  },
  async mounted() {
    await this.refreshAll();
  },
  methods: {
    async refreshAll() {
      this.busy = true;
      this.createError = "";
      this.apiError = "";
      try {
        const [defaults, distros, uploads, routes] = await Promise.all([
          getDefaultSoftware(),
          getDistributions(),
          listUploads(),
          listRoutes()
        ]);
        this.defaultSoftware = defaults.default_software || [];
        this.distributions = distros.distributions || [];
        this.uploads = uploads.uploads || [];
        this.routes = routes;
        if (this.selectedId) {
          await this.selectUpload(this.selectedId);
        }
      } catch (e) {
        this.createError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async loadRoutes() {
      this.busy = true;
      this.apiError = "";
      try {
        this.routes = await listRoutes();
      } catch (e) {
        this.apiError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    clearSearch() {
      this.searchResults = [];
      this.searchCount = 0;
      this.searchError = "";
      this.searchResetKey += 1;
    },
    async runSearch(params) {
      this.busy = true;
      this.searchError = "";
      try {
        const resp = await searchUploads(params);
        this.searchResults = resp.uploads || [];
        this.searchCount = resp.count || 0;
      } catch (e) {
        this.searchError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async onCreate(payload) {
      this.busy = true;
      this.createError = "";
      try {
        let resp;
        if (payload && payload.mode === "distribution") {
          resp = await createFromDistribution({
            distributionId: payload.distributionId,
            software: payload.software,
            customSoftware: payload.customSoftware
          });
        } else {
          resp = await uploadIso(payload);
        }
        const upload = resp.upload;
        this.createResetKey += 1;
        await this.refreshAll();
        if (upload && upload.id) {
          await this.selectUpload(upload.id);
        }
      } catch (e) {
        this.createError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async selectUpload(id) {
      this.busy = true;
      this.editError = "";
      try {
        this.selectedId = id;
        const resp = await getUpload(id);
        this.selected = resp.upload;
        this.manifest = null;
      } catch (e) {
        this.editError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async onSaveSoftware(payload) {
      if (!this.selected) return;
      this.busy = true;
      this.editError = "";
      try {
        const resp = await updateSoftware(this.selected.id, payload);
        this.selected = resp.upload;
        await this.refreshAll();
      } catch (e) {
        this.editError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async loadManifest() {
      if (!this.selected) return;
      this.busy = true;
      this.editError = "";
      try {
        const resp = await getInstallManifest(this.selected.id);
        this.manifest = resp.install;
      } catch (e) {
        this.editError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async onDelete() {
      if (!this.selected) return;
      this.busy = true;
      this.editError = "";
      try {
        await deleteUpload(this.selected.id);
        this.selected = null;
        this.selectedId = null;
        this.manifest = null;
        await this.refreshAll();
      } catch (e) {
        this.editError = String(e.message || e);
      } finally {
        this.busy = false;
      }
    }
  }
};
</script>

<style scoped>
.wrap {
  max-width: 1100px;
  margin: 24px auto;
  padding: 0 16px;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  color: #111;
}

.grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

.detail {
  margin-top: 16px;
}
</style>
