<script setup lang="ts">
import { onMounted, Ref } from '@vue/runtime-core';
import { ref} from 'vue';
import { QForm, useQuasar } from "quasar";
import axiosBase, { AxiosError } from "axios"

const quasar = useQuasar();

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
  const data:any = error.response?.data;
  const errMsg = data?.err_msg || "不明なエラーが発生しました";

  // 失敗時はエラーを通知
  quasar.notify(
    {
      message: errMsg,
      color: "negative"
    }
  )
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
// validation
const isExist = (valName:string) => {
  return (val:any) => {
    return !["", null, undefined].includes(val) || `${valName}を入力してください`;
  };
};
const isNumber = (valName:string) => {
  return (val:string) => {
    return Number.isFinite(Number(val)) || `${valName}は数値を入力してください`;
  };
};
const isLatitude = (val:string) => {
  return (-90 <= Number(val) && Number(val) <= 90) || "緯度は90以下を入力してください";
};
const isLongitude = (val:string) => {
  return (-180 <= Number(val) && Number(val) <= 180) || "経度は180以下を入力してください";
};
const validationRules = {
  lat: [isExist(labels.lat), isNumber(labels.lat), isLatitude],
  lon: [isExist(labels.lon), isNumber(labels.lon), isLongitude]
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
});

const formatDispDate = (date:string):string => {
  const splited = date.split("-");
  return `${splited[1]}/${splited[2]}`
};

const forecast = async () => {
  if(!locationForm.value)return;
  locationForm.value.validate().then(async (success:boolean) => {
    if(!success)return;

    const response = await axios.get("", {
      params:{lat: locationFormValue.value.lat, lon: locationFormValue.value.lon}
    });
    if(!response)return;
    // 開花日・満開日を画面に表示
    forecastData.value.kaikaDate = response.data.kaika_date;
    forecastData.value.mankaiDate = response.data.mankai_date;
    forecastData.value.isShow = true;
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
    <q-layout view="lHh lpr lFf" container style="height: 400px">
      <q-header elevated class="bg-pink">
        <q-toolbar>
          <q-img src="/favicon.white.svg" alt="桜アイコン" class="cherry-icon q-mx-sm"></q-img>
          <span class="text-h6">サクラサク？｜桜の開花予測</span>
        </q-toolbar>
      </q-header>
      <q-page-container>
        <q-page class="q-pa-md">
          <div class="row justify-center">
            <div class="col-12 col-sm-6 col-lg-4">

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
              <q-btn
                icon="eco"
                color="pink"
                @click="forecast"
                label="開花日を予測"
                class="full-width"
              ></q-btn>
              <div class="col-12" v-if="forecastData.isShow">
                <div class="row q-py-md">
                  <div class="col-6 q-pa-xs text-center">
                    <div class="text-h5">開花日</div>
                    <div>
                      <span class="text-h4">{{ formatDispDate(forecastData.kaikaDate) }}</span>ごろ
                    </div>
                    
                  </div>
                  <div class="col-6 q-pa-xs text-center">
                    <div class="text-h5">満開日</div>
                    <div>
                      <span class="text-h4">{{ formatDispDate(forecastData.mankaiDate) }}</span>ごろ
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </q-page>
      </q-page-container>

    </q-layout>
    <q-ajax-bar
      position="bottom"
      color="transparent"
      size="10px"
      @start="isLoading = true"
      @stop="isLoading = false"
    />
    <q-inner-loading :showing="isLoading">
      <q-spinner-dots size="50px" color="pink" />
    </q-inner-loading>

        
  </div>


</template>

<style scoped>
.cherry-icon{
  width:24px;
  height:24px;
}
</style>
