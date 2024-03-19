<script setup lang="ts">
import { onMounted, Ref } from '@vue/runtime-core';
import { ref} from 'vue';
import { QForm} from "quasar";
import axiosBase, { AxiosError } from "axios"

const axios = axiosBase.create({
  baseURL: import.meta.env.VITE_FUNCTIONS_URL,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  },
  responseType: 'json'
});
// インターセプターを利用したエラー処理ハンドリング
axios.interceptors.response.use((response) => {
  // 成功時は普通にresponse返却
  return response;
}, (error:AxiosError) => {
  console.log(error);
  const statusCode = error.response?.status || null;
  const data:any = error.response?.data;
  const errMsg = data?.err_msg || "不明なエラーが発生しました";

  // TODO:失敗時はエラー表示
});

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

const getCurrentPosition = ():Promise<GeolocationPosition> => {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      position => resolve(position),
      error => reject(error)
    );
  })
}

const forecastData = ref({
  isShow: false,
  kaikaDate: "",
  mankaiDate: ""
})

const forecast = async () => {
  if(!locationForm.value)return;
  locationForm.value.validate().then(async (success:boolean) => {
    if(!success)return;

    const response = await axios.get("", {
      params:{lat: locationFormValue.value.lat, lon: locationFormValue.value.lon}
    })
    if(!response)return;
    // 開花日・満開日を画面に表示
    forecastData.value.kaikaDate = response.data.kaika_date;
    forecastData.value.mankaiDate = response.data.mankai_date;
    forecastData.value.isShow = true;
    console.log(response.data)
  });


};

const isLoading = ref(false);

onMounted(async () => {
  const position = await getCurrentPosition();
  if(!position) return;

  // 位置情報取得できた場合はセットしてAPI叩く
  locationFormValue.value.lat = position.coords.latitude;
  locationFormValue.value.lon = position.coords.longitude;
  forecast();
});
</script>

<template>
  <div>

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
      <div class="row">
      </div>
    </q-form>
    <q-btn
      icon="eco"
      @click="forecast"
      label="開花日を予測"
    >
    </q-btn>

    <div class="col-12 q-pa-xs" v-if="forecastData.isShow">
      <div>開花日 {{ forecastData.kaikaDate }}ごろ</div>
      <div>満開日 {{ forecastData.mankaiDate }}ごろ</div>
    </div>
    <q-ajax-bar
      position="bottom"
      color="transparent"
      size="10px"
      @start="isLoading = true"
      @stop="isLoading = false"
    />
    <q-inner-loading :showing="isLoading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
  <!-- TODO:header -->
</template>

<style scoped>
</style>
