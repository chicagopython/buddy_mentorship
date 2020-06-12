function autocomplete(input_id) {
  $(`#${input_id}`).autocomplete({
    source: "/skill",
  });
}
