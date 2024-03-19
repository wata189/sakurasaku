<script setup lang="ts">
import { onMounted, Ref } from '@vue/runtime-core';
import { ref} from 'vue';
import { QForm} from "quasar";

const locationForm:Ref<QForm | undefined> = ref();

type LocationFormValue = {
  lat: number | null,
  lon: number | null
}
const locationFormValue:Ref<LocationFormValue> = ref({
  lat: null,
  lon: null
});

const labels = {
  lat: "緯度",
  lon: "経度"
};

const validationRules = {
  lat: [],
  lon: []
};

onMounted(() => {
  console.log("start sakurasaku")
});
</script>

<template>
  <!-- TODO:header -->
  <q-form ref="locationForm">
    <div class="row">
      <div class="col-6 q-pa-xs">
        <q-input
          v-model="locationFormValue.lat"
          type="number"
          :label="labels.lat"
          :rules="validationRules.lat"
          clearable
        ></q-input>
      </div>
      <div class="col-6 q-pa-xs">
        <q-input
          v-model="locationFormValue.lon"
          type="number"
          :label="labels.lon"
          :rules="validationRules.lon"
          clearable
        ></q-input>
      </div>
    </div>
  </q-form>
  sakurasaku
</template>

<style scoped>
</style>
