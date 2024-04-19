<script setup lang="ts">
import { onMounted, Ref } from '@vue/runtime-core';
import { computed, ref} from 'vue';
import { QForm, useQuasar } from "quasar";
import axiosBase, { AxiosError } from "axios"
import SakuraDispDate from '@/components/SakuraDispDate.vue';

import facviconWhite from "./assets/favicon.white.svg"
const FAVICON_WHITE = facviconWhite;

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


// 市区町村マスタはJsonから読み込み
import citiesJson from "./assets/cities.json";
type City = {
    id: number;
    lat: number;
    lon: number;
    name: string;
  }
const cities:City[] = citiesJson.cities;

// 入力された文字を使用して市区町村マスタをフィルタリング
const city = ref("");
const filteredCities = computed(() => {
  return cities.filter(c => {
    return c.name.includes(city.value);
  });
});

/**
 * 市区町村の緯度経度をフォームに入力する処理
 * @param {City} city - 市区町村
 */
const setPosition = (city:City) => {
  locationFormValue.value.lat = city.lat;
  locationFormValue.value.lon = city.lon;
  forecast();
};


// フォーム要素の参照
const locationForm:Ref<QForm | undefined> = ref();
type LocationFormValue = {
  lat: number | null,
  lon: number | null
}
// フォームの書く要素にバインドして入力値を受け取る
const locationFormValue:Ref<LocationFormValue> = ref({
  lat: null,
  lon: null
});

// フォーム要素のラベル
const labels = {
  lat: "緯度",
  lon: "経度"
};

// フォーム要素のバリデーション処理
// quasarのコンポーネントの仕様で、 「true/falseを返すチェック処理 || エラーメッセージ」 の形式にする
/**
 * 値が存在することをチェックする処理
 * カリー化を利用し、エラーメッセージ内の変数名を自由に変更できるようにする
 * @param {string} valName - チェックする値の名前
 * @returns {function(val: string): true | string} - 値が存在することをチェックする関数
 */
const isExist = (valName:string) => {
  return (val:any) => {
    return !["", null, undefined].includes(val) || `${valName}を入力してください`;
  };
};
/**
 * 値が数値であることをチェックする処理
 * カリー化を利用し、エラーメッセージ内の変数名を自由に変更できるようにする
 * @param {string} valName - チェックする値の名前
 * @returns {function(val: string): true | string} - 値が数値であることをチェックする関数
 */
const isNumber = (valName:string) => {
  return (val:string) => {
    return Number.isFinite(Number(val)) || `${valName}は数値を入力してください`;
  };
};
/**
 * 値が緯度であることをチェックする処理
 * @param {string} val - チェックする数値（文字列型）
 * @returns {true | string} - 値が-90~90であればtrueを、そうでなければエラーメッセージを返す
 */
const isLatitude = (val:string) => {
  return (-90 <= Number(val) && Number(val) <= 90) || "緯度は90以下を入力してください";
};
/**
 * 値が経度であることをチェックする処理
 * @param {string} val - チェックする数値（文字列型）
 * @returns {true | string} - 値が-180~180であればtrueを、そうでなければエラーメッセージを返す
 */
const isLongitude = (val:string) => {
  return (-180 <= Number(val) && Number(val) <= 180) || "経度は180以下を入力してください";
};

// フォームに設定するバリデーションルール
const validationRules = {
  lat: [isExist(labels.lat), isNumber(labels.lat), isLatitude],
  lon: [isExist(labels.lon), isNumber(labels.lon), isLongitude]
};

/**
 * 位置情報を取得する処理
 * Promiseで包んでasync/awaitなど利用できるようにする
 * @returns {Promise<GeolocationPosition>} - 位置情報を持ったPromiseオブジェクト
 */
const getCurrentPosition = ():Promise<GeolocationPosition> => {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      position => resolve(position),
      error => reject(error)
    );
  })
}

// 予測結果
const forecastData = ref({
  isShow: false,
  kaikaDate: "",
  mankaiDate: ""
});

/**
 * 位置情報から開花日・満開日の予測を行う
 * @async
 * @returns {Promise<void>} - asyncなので空のPromiseを返却
 */
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

// ローディング状態を格納
const isLoading = ref(false);

onMounted(async () => {
  const position = await getCurrentPosition();
  if(!position) return; // 位置情報取得できなかったら画面表示のみ

  // 位置情報取得できた場合はセットして予測API叩く
  locationFormValue.value.lat = position.coords.latitude;
  locationFormValue.value.lon = position.coords.longitude;
  forecast();
});
</script>

<template>
  <div>
    <q-layout view="lHh lpr lFf" container style="min-height: 600px">
      <q-header elevated class="bg-pink">
        <q-toolbar>
          <q-img :src="FAVICON_WHITE" alt="桜アイコン" class="cherry-icon q-mx-sm"></q-img>
          <span class="text-h6">サクラサク？</span><span class="text-h6 gt-xs">｜桜の開花予測</span>
        </q-toolbar>
      </q-header>
      <q-page-container>
        <q-page class="q-pa-md">
          <div class="row justify-center">
            <div class="col-12 col-sm-6 col-lg-4">
              <!-- 位置情報の入力 -->
              <q-form ref="locationForm">
                <div class="row items-center">
                  <div class="col-4 col-md-5 q-pa-xs">
                    <q-input
                      v-model="locationFormValue.lat"
                      type="number"
                      :label="labels.lat"
                      :rules="validationRules.lat"
                      clearable
                    ></q-input>
                  </div>
                  <div class="col-4 col-md-5 q-pa-xs">
                    <q-input
                      v-model="locationFormValue.lon"
                      type="number"
                      :label="labels.lon"
                      :rules="validationRules.lon"
                      clearable
                    ></q-input>
                  </div>
                  <div class="col-4 col-md-2 q-pa-xs">
                    <!-- 市区町村検索 -->
                    <q-btn-dropdown
                      class="full-width"
                      color="pink"
                      icon="search"
                    >
                      <div class="bg-pink-2">
                        <q-input
                          v-model="city"
                          placeholder=位置情報を入力
                          class="q-pa-xs"
                          dense
                        ></q-input>
                        <q-separator></q-separator>
                        <q-scroll-area style="height:300px;">
                          <q-list>
                            <q-item v-for="city in filteredCities" clickable v-close-popup @click="setPosition(city)">
                              <q-item-section>
                                <q-item-label>{{ city.name }}</q-item-label>
                              </q-item-section>
                            </q-item>
                          </q-list>
                        </q-scroll-area>
                      </div>
                    </q-btn-dropdown>
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

              <!-- 結果表示 -->
              <div class="col-12" v-if="forecastData.isShow">
                <div class="row q-py-md" v-if="forecastData.isShow">
                  <div class="col-6 q-pa-xs">
                    <sakura-disp-date
                      title="開花日"
                      :date="forecastData.kaikaDate"
                    >
                    </sakura-disp-date>
                  </div>
                  <div class="col-6 q-pa-xs">
                    <sakura-disp-date
                      title="満開日"
                      :date="forecastData.mankaiDate"
                    >
                    </sakura-disp-date>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </q-page>
      </q-page-container>

    </q-layout>

    <!-- q-ajax-bar+inner-loadingの組み合わせで、ajax時にローディングを表示 -->
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
