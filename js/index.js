import { FrameToFrame, FrameToStream, StreamToStream, createEvent } from "../../../core/client/client.js";
import { segment } from "oicq";

export const rule = {
  bh3_bind: {
    reg: "^#崩坏三绑定",
    priority: 800,
    describe: "绑定账号",
  },
  bh3_cookie: {
    reg: "^#崩坏三cookie",
    priority: 800,
    describe: "绑定崩坏三米游社cookie",
  },
  bh3_card: {
    reg: "^#崩坏三卡片",
    priority: 800,
    describe: "获取卡片",
  },
  bh3_character: {
    reg: "^#崩坏三女武神",
    priority: 800,
    describe: "获取女武神",
  },
  bh3_finance: {
    reg: "^#崩坏三手账",
    priority: 800,
    describe: "崩坏三手账",
  },
  bh3_sign: {
    reg: "^#崩坏三(自动)?签到",
    priority: 800,
    describe: "崩坏三自动签到",
  },
  bh3_sign_all: {
    reg: "^#崩坏三全部签到",
    priority: 800,
    describe: "崩坏三手动全部签到",
  },
};

export async function bh3_bind(e) {
  FrameToFrame({
    _package: "bh3",
    _handler: "bind",
    params: {
      event: await createEvent(e),
      message: e.msg.replace("#崩坏三绑定", ""),
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {
        let img = response.image;
        if (img.length) {
          e.reply([response.message, segment.image(img)]);
        } else {
          e.reply(response.message);
        }
      }
    },
  });

  return true;
}

export async function bh3_cookie(e) {
  if (!e.isPrivate) return;

  let cookie = e.msg.replace("#崩坏三cookie", "");
  let param = cookie.match(/account_id=(\w{0,9})|cookie_token=([^;]+)/g);
  let token = {};
  for (let val of param) {
    let tmp = val.split("=");
    token[tmp[0]] = tmp[1];
  }
  FrameToFrame({
    _package: "bh3",
    _handler: "cookie",
    params: {
      event: await createEvent(e),
      messageDict: token,
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {
        let img = response.image;
        if (img.length) {
          e.reply([response.message, segment.image(img)]);
        } else {
          e.reply(response.message);
        }
      }
    },
  });

  return true;
}

export async function bh3_card(e) {
  FrameToStream({
    _package: "bh3",
    _handler: "bh3_player_card",
    params: {
      event: await createEvent(e),
      message: e.msg.replace("#崩坏三卡片", ""),
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {

        let msg;
        if (response.messageDict.at) {
          msg = [segment.at(response.messageDict.at)];
        } else {
          msg = [];
        }

        if (response.image.length) {
          msg.push(segment.image(response.image));
        } else {
          msg.push(response.message);
        }
        e.reply(msg);
      }
    },
  });
  return true;
}

export async function bh3_character(e) {
  FrameToStream({
    _package: "bh3",
    _handler: "bh3_chara_card",
    params: {
      event: await createEvent(e),
      message: e.msg.replace("#崩坏三女武神", ""),
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {

        let msg;
        if (response.messageDict.at) {
          msg = [segment.at(response.messageDict.at)];
        } else {
          msg = [];
        }

        if (response.image.length) {
          msg.push(segment.image(response.image));
        } else {
          msg.push(response.message);
        }
        e.reply(msg);
      }
    },
  });
  return true;
}

export async function bh3_finance(e) {
  FrameToFrame({
    _package: "bh3",
    _handler: "show_finance",
    params: {
      event: await createEvent(e),
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {
        let img = response.image;
        if (img.length) {
          e.reply([response.message, segment.image(img)]);
        } else {
          e.reply(response.message);
        }
      }
    },
  });

  return true;
}

export async function bh3_sign(e) {
  FrameToFrame({
    _package: "bh3",
    _handler: "switch_autosign",
    params: {
      event: await createEvent(e),
      message: e.msg.replace(/^#崩坏三(自动)?签到/g, ""),
    },
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {
        e.reply(response.message);
      }
    },
  });

  return true;
}

export async function bh3_sign_all(e) {
  if (!e.isMaster) return;
  FrameToStream({
    _package: "bh3",
    _handler: "reload_sign",
    onData(error, response) {
      if (error) {
        console.log(error.stack);
      } else {
        e.reply(response.message);
      }
    },
  });

  return true;
}