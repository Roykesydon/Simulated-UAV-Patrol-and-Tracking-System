<template>
  <!-- draw 100*100 grid -->
  <div class="d-flex align-center justify-center home" style="height: 100%">
    <v-card
      class="uav-bar mr-10 pa-5 rounded-xl side-card"
      width="300px"
      height="40em"
      color="primary_dark"
    >
      <div class="text-h5 mb-5">UAV Status</div>
      <v-card color="#101010" class="pa-3" style="height: 33em">
        <v-card
          class="my-3 pa-1"
          height="7em"
          :color="drone.color"
          v-for="drone in drones"
        >
          <v-container>
            <v-row>
              <v-col cols="7">
                <div style="font-family: 'Noto Sans TC', sans-serif">
                  {{ drone.name }}
                </div>

                <v-chip
                  class="ma-2"
                  :color="droneStatusColor(drone.status)"
                  variant="flat"
                  text-color="white"
                >
                  {{ mappingStatus(drone.status) }}
                </v-chip>
              </v-col>
              <v-col cols="5">
                <v-img :src="drone.img"></v-img>
              </v-col>
            </v-row>
          </v-container>
        </v-card>
      </v-card>
    </v-card>
    <div class="grid">
      <div
        v-for="i in 100"
        :key="i"
        class="row"
        :class="{
          'grid-bottom-border': i % 10 === 0,
          'grid-top-border': i === 1,
        }"
      >
        <!-- every ten row draw a line -->
        <div
          v-for="j in 100"
          :key="j"
          class="cell d-flex align-center justify-center"
          :class="{
            'grid-right-border': j % 10 === 0,
            'grid-left-border': j === 1,
          }"
        >
          <div class="" v-if="i === 50 && j === 50">
            <v-img
              width="70"
              :aspect-ratio="1"
              cover
              src="../assets/embassy.png"
            ></v-img>
          </div>
          <div
            class=""
            v-if="i === humanPosition[0] + 1 && j === humanPosition[1] + 1"
          >
            <div
              :class="targetIsBeingTracked ? '' : 'gray-filter'"
              style="left: -25px; top: -25px; position: relative"
            >
              <img src="../assets/suspicious.png" class="patrol-drone" />
            </div>
          </div>
          <!-- v-for with index -->
          <div v-for="(drone, index) in drones" :key="index">
            <div
              class=""
              v-if="
                i === dronePosition[index][0] + 1 &&
                j === dronePosition[index][1] + 1
              "
            >
              <div style="left: -25px; top: -25px; position: relative">
                <img :src="drone.img" class="patrol-drone img-white-border" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <v-card
      class="uav-bar ml-10 pa-5 rounded-xl side-card"
      width="300px"
      height="40em"
      color="primary_dark"
    >
      <div class="text-h5 mb-5">Event Notification</div>
      <v-card
        color="#101010"
        class="pa-3"
        style="height: 33em; overflow-y: scroll"
      >
        <div
          v-for="notification in notificationList"
          :key="notification.time + notification.app_name + notification.event"
        >
          <v-card class="my-3 pa-3 pt-0" :color="notification.level">
            <div class="text-h5 mb-0">
              <v-container>
                <v-row class="d-flex align-center">
                  <v-col cols="4" class="ma-0 py21 pl-0 mr-0 pr-3">
                    <v-img
                      :aspect-ratio="1"
                      cover
                      :src="getNotificationIcon(notification.level)"
                    />
                  </v-col>
                  <v-col cols="8" class="d-flex justify-start pa-2">
                    {{ getNotificationTitle(notification.level) }}
                  </v-col>
                </v-row>
              </v-container>
            </div>
            <div class="notification-detail">
              <div>
                回報：{{ getNotificationDroneName(notification.app_name) }}
              </div>
              <div>事件：{{ getNotificationEvent(notification.event) }}</div>
              <div>時間：{{ notification.time }}</div>
            </div>
          </v-card>
        </div>
      </v-card>
    </v-card>
  </div>
</template>

<script lang="ts" setup>
// import HelloWorld from "@/components/HelloWorld.vue";
import { reactive, ref } from "vue";

// Notifcation
const getNotificationIcon = (level: string) => {
  if (level === "error") return "/src/assets/alarm.png";
  else if (level === "success") return "/src/assets/check.png";
  else if (level === "info") return "/src/assets/info.png";
};
const getNotificationTitle = (level: string) => {
  if (level === "error") return "Warning";
  else if (level === "success") return "Success";
  else if (level === "info") return "Info";
};
const getNotificationDroneName = (app_name: string) => {
  if (app_name === "track_drone_1") return "追蹤一號機";
  else if (app_name === "patrol_drone_1") return "巡邏一號機";
  else if (app_name === "patrol_drone_2") return "巡邏二號機";
  else if (app_name === "patrol_drone_3") return "巡邏三號機";
};
const getNotificationEvent = (event: string) => {
  if (event === "FOUND_TARGET") return "偵測到可疑人員";
  else if (event === "START_PATROLLING") return "開始巡邏";
  else if (event === "TARGET_LEFT") return "可疑人員已離開警戒區";
};

// Drone status
const mappingStatus = (status: string) => {
  if (status === "WAITING_FOR_COMMAND") return "待命中";
  else if (status === "PATROLLING") return "巡邏中";
  else if (status === "TRACKING") return "追蹤中";
  else if (status === "BACKING_TO_BASE") return "返航中";
  else if (status === "SEARCHING") return "搜索中";
};

const droneStatusColor = (status: string) => {
  if (status === "WAITING_FOR_COMMAND") return "#3f51b5";
  else if (status === "PATROLLING") return "#17a46b";
  else if (status === "TRACKING") return "#eb9638";
  else if (status === "BACKING_TO_BASE") return "#3f51b5";
  else if (status === "SEARCHING") return "#eb9638";
};

let drones = reactive([
  {
    name: "追蹤一號機",
    status: "WAITING_FOR_COMMAND",
    color: "primary",
    img: "/src/assets/track-drone.png",
  },
  {
    name: "巡邏一號機",
    status: "WAITING_FOR_COMMAND",
    color: "secondary",
    img: "/src/assets/patrol-drone.png",
  },
  {
    name: "巡邏二號機",
    status: "WAITING_FOR_COMMAND",
    color: "secondary",
    img: "/src/assets/patrol-drone.png",
  },
  {
    name: "巡邏三號機",
    status: "WAITING_FOR_COMMAND",
    color: "secondary",
    img: "/src/assets/patrol-drone.png",
  },
]);

let humanPosition = reactive([-1, -1]);
let notificationList: any[] = reactive([]);
let dronePosition: any[] = reactive([
  [-1, -1],
  [-1, -1],
  [-1, -1],
  [-1, -1],
]);
let targetIsBeingTracked = ref(false);

const IN_API_URL = "http://localhost:8127";

// fetch human position
setInterval(() => {
  fetch("http://localhost:8122/human/position")
    .then((res) => res.json())
    .then((data) => {
      console.log(humanPosition);
      humanPosition[0] = data.position[0];
      humanPosition[1] = data.position[1];
    });
}, 700);

// fetch track drone position
setInterval(() => {
  fetch("http://localhost:8126/0/position")
    .then((res) => res.json())
    .then((data) => {
      dronePosition[0][0] = data.position[0];
      dronePosition[0][1] = data.position[1];
    });
}, 700);

// fetch patrol drone position
for (let i = 1; i <= 3; i++) {
  setInterval(() => {
    fetch("http://localhost:8125" + "/" + (i - 1) + "/position")
      .then((res) => res.json())
      .then((data) => {
        dronePosition[i][0] = data.position[0];
        dronePosition[i][1] = data.position[1];
      });
  }, 700);
}

// fetch notification
setInterval(() => {
  fetch(IN_API_URL + "/notification")
    .then((res) => res.json())
    .then((data) => {
      notificationList = data;
    });
}, 700);

// fetch drone status
setInterval(() => {
  fetch("http://localhost:8126/0/status")
    .then((res) => res.json())
    .then((data) => {
      drones[0]["status"] = data.status;
    });
}, 700);
for (let i = 0; i < 3; i++) {
  setInterval(() => {
    fetch("http://localhost:8125" + "/" + i + "/status")
      .then((res) => res.json())
      .then((data) => {
        drones[i + 1]["status"] = data.status;
      });
  }, 700);
}

// fetch target is being tracked
setInterval(() => {
  let trackFlag = false;
  for (let i = 0; i < 4; i++) {
    if (drones[i]["status"] === "TRACKING") {
      trackFlag = true;
      break;
    }
  }
  targetIsBeingTracked.value = trackFlag;
}, 700);
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@200;300&display=swap");

.grid-bottom-border {
  border-bottom: 1px solid var(--gird-border-color);
}

.grid-top-border {
  border-top: 1px solid var(--gird-border-color);
}

.grid-right-border {
  border-right: 1px solid var(--gird-border-color);
}

.grid-left-border {
  border-left: 1px solid var(--gird-border-color);
}

/* .home {
  background-image: linear-gradient(
    to right bottom,
    #071c39,
    #08182d,
    #091222,
    #050c17,
    #010307
  );
} */

.img-white-border {
  -webkit-filter: drop-shadow(0px 1px 0 white) drop-shadow(0px -1px 0 white) drop-shadow(1px 0px 0 white) drop-shadow(-1px 0px 0 white);
  filter: drop-shadow(0px 1px 0 white) drop-shadow(0px -1px 0 white) drop-shadow(1px 0px 0 white) drop-shadow(-1px 0px 0 white);
}

.notification-detail {
  color: white;
  font-size: 0.9em;
  font-family: "Noto Sans TC", sans-serif;
}

.patrol-drone {
  width: 50px;
  height: 50px;
  position: absolute;
  z-index: 3;
}

.gray-filter {
  filter: grayscale(100%);
}
.side-card {
  background-color: rgb(45, 45, 45);
}

.human {
  position: relative;
  z-index: 2;
}

.grid {
  /* --gird-border-color: rgb(72, 111, 148); */
  --gird-border-color: rgb(105, 148, 187);
  width: 40em;
  height: 40em;
  /* border: 1px solid black; */
  display: flex;
  flex-direction: column;
}

.row {
  display: flex;
  flex-direction: row;
}

.cell {
  width: 0.4em;
  height: 0.4em;
  background-color: black;
  /* with border */
  /* border: 1px solid white; */
}

/* scroll bar*/
/* custom scrollbar */
::-webkit-scrollbar {
  width: 20px;
  background-color: #101010;
}

::-webkit-scrollbar-track {
  background-color: #101010;
}

::-webkit-scrollbar-thumb {
  /* background-color: #d6dee1; */
  /* background: linear-gradient(-45deg, #23a6d5, #23d5ab);
   */
  background: #a8bbbf;
  animation: gradient 1s ease infinite;
  border-radius: 20px;
  border: 6px solid #101010;
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #a8bbbf;
}

/**/
</style>
